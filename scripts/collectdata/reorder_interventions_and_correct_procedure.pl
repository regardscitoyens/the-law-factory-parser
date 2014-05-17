#!/usr/bin/perl

use strict;

my $dir = shift();
my $debug = shift();
if (!$dir) {
    print STDERR "ERROR: Pocedure directory need as argument\n";
    exit 1;
}

open CSV, "$dir/procedure.csv";
my $procedure = {};
my @row;
while ((@row = split(/;/, <CSV>)) && ($#row > 10)) {
        chomp($row[$#row]);
	$row[13] =~ s/-//g;
	$row[14] =~ s/-//g;
	@{$procedure->{$row[6]}} = @row;
}
close CSV;

my @keys = keys %{$procedure};
if ($#keys == -1) {
    print STDERR "ERROR: No procedure found\n";
    exit 2;
}

my $csvchanged = 0;

open INT, "ls $dir/*/interventions/*.xml |";
while (<INT>) {
    chomp;
    if (/\/(..)_[^_]*_([^_]*)_[^_]*\/interventions\/(\d{4})-(\d{2})-(\d{2})/) {
	my $id = $1;
	my $previd = 0;
	$previd = sprintf("%02d", $id -1) if ($id + 0);
	my $nextid = sprintf("%02d", $id +1);
	my $date = $3.$4.$5;
	my $chambre = $2;
	if ($procedure->{$id}[13] > $date) {
	    if ($previd && $procedure->{$previd}[14] <= $date) {
		$procedure->{$id}[13] = $date;
		$csvchanged = 1;
		print STDERR "INFO: change beginning date of $id thanks to $_\n" if ($debug);
	    }else{
		print STDERR "ERROR: PB beginnig \t $_ (".$procedure->{$id}[13]." < $date < ".$procedure->{$id}[14].")\n";
	    }
	}
	if ($procedure->{$id}[14] < $date) {
	    if ($procedure->{$nextid}[13] >= $date) {
		$procedure->{$id}[14] = $date;
		$csvchanged = 1;
		print STDERR "INFO: change ending date of $id thanks to $_\n" if ($debug);
	    }else{
		my $testid = $id; my $solved = 0;
		for (my $i = $id+0 ; ($testid = sprintf('%02d', $i)) && $procedure->{$testid} ; $i++ ) {
		    my $testprevid = sprintf('%02d', $i - 1);
		    my $testnextid = sprintf('%02d', $i + 1);
		    if ($procedure->{$testprevid}[14] <= $date && $procedure->{$testnextid}[13] >= $date && $procedure->{$testid}[9] eq $chambre) {
			my $location = $dir.'/'.$testid.'_'.$procedure->{$testid}[8].'_'.$procedure->{$testid}[9].'_'.$procedure->{$testid}[10].'/interventions/';
			$location =~ s/ //g;
			mkdir ($location);
			my $file = $_;
			system("mv $file $location");
			$file =~ s/csv$/xml/;
			system("mv $file $location");
			$file =~ s/xml$/json/;
			system("mv $file $location");
			print STDERR "INFO: NEW Location ".$location." found for $file & co\n" if ($debug);
			$solved = 1;
		    }
		    if ($solved) {
			if ($procedure->{$testid}[13] > $date) {
			    $procedure->{$testid}[13] = $date;
			    $csvchanged = 1;
			    print STDERR "INFO: change beginning date of $testid thanks to $_\n" if ($debug);
			}
			if ($procedure->{$testid}[14] < $date) {
			    $procedure->{$testid}[14] = $date;
			    $csvchanged = 1;
			    print STDERR "INFO: change ending date of $testid thanks to $_\n" if ($debug);
			}
			last;
		    }
		}
		print STDERR "ERROR: PB ending \t $_ (".$procedure->{$id}[13]." < $date < ".$procedure->{$id}[14].")\n" unless($solved);
	    }
	}
    }
}
close(INT);

if ($csvchanged) {
    open CSV, "> $dir/procedure.csv";
    foreach my $id (sort {$procedure->{$a}[6] cmp $procedure->{$b}[6]} keys(%{$procedure})) {
	$procedure->{$id}[13] =~ s/(....)(..)(..)/\1-\2-\3/;
	$procedure->{$id}[14] =~ s/(....)(..)(..)/\1-\2-\3/;
	print CSV join(';', @{$procedure->{$id}})."\n";
    }
    close CSV;
    print STDERR "INFO: $dir/procedure.csv CHANGED\n" if ($debug);
}
