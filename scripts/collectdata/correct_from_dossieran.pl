#!/usr/bin/perl

use WWW::Mechanize;
use utf8;
use strict;

my $procedure = [];
my $i = 0;
my @row;
while ((@row = split(/;/, <STDIN>)) && ($#row > 10)) {
        chomp($row[$#row]);
	@{$procedure->[$i++]} = @row;
}

if (!($#{$procedure}+1) && !$procedure->[0][4] || !$procedure->[0][3]) {
  print STDERR "WARNING: no dossier AN found, skipping corrector\n";
  exit(0);
}

my $url = "http://www.assemblee-nationale.fr/".$procedure->[0][3]."/dossiers/".$procedure->[0][4].".asp";
my $a = WWW::Mechanize->new();
$a->get($url);
my $content = $a->content;
utf8::encode($content);
my %mois = ('janvier'=>'01', 'fvrier'=>'02', 'mars'=>'03', 'avril'=>'04', 'mai'=>'05', 'juin'=>'06', 'juillet'=>'07', 'aot'=>'08', 'septembre'=>'09','octobre'=>'10','novembre'=>'11','dcembre'=>'12');
my @steps = ();
my $section; my $chambre; my $stade; my $date; my $mindate = '99999999'; my $maxdate; my $hasetape = 0; my $canparse = 0;
foreach (split(/\n/, $content)) {
    s/\r//g;
    s/mis en ligne le \d+ \S+//;
    if (/<hr>.*Loi/) {
	$canparse = 0;
	if (/organique/i && $procedure->[0][1] =~ /organique/i) {
	    $canparse = 1;
	}elsif (!/organique/i && $procedure->[0][1] !~ /organique/i) {
	    $canparse = 1;
	}
    }
    unless ($canparse) {
	next;
    }
    if (s/.*<a name="ETAPE[^"]+">((<a[^>]+>|<i>|<\/i>|<br\/?>|<\/a>|<sup>|<\/sup>|<\/font>|<\/b>|[^>])+)<\/p>(.*)//) {
	$section = $1;
	$hasetape = 1;
	$section =~ s/<[^>]+>//g;
	if ($section =~ /assembl..?e nationale/i) {
	    $chambre = "assemblee";
	}elsif($section =~ /s..?nat/i) {
	    $chambre = "senat";
	}elsif($section =~ /(CMP|Commission Mixte Paritaire)/i) {
	    $chambre = 'CMP';
	}
	$stade = 'depot';
    }elsif(/<b>/) {
	if (/publique/i) {
	    $stade = "hemicycle";
	}elsif (/commission/i) {
	    $stade = "commission";
	}
    }elsif(!/nomm..? |nomination/i && / (\d+) (janvier|f..?vrier|mars|avril|mai|juin|juillet|ao..?t|septembre|octobre|novembre|d..?cembre) (20\d+)/ && $chambre && $stade && !$date) {
	my $annee = $3; my $mois = $2; my $jour = sprintf('%02d', $1);
	lc($mois);
	$mois =~ s/[^a-z]+//i;
	$date = "$annee-".$mois{$mois}."-$jour";
    }
    if($hasetape && / (\d+) (janvier|f..?vrier|mars|avril|mai|juin|juillet|ao..?t|septembre|octobre|novembre|d..?cembre) (20\d+)/) {
	my $annee = $3; my $mois = $2; my $jour = sprintf('%02d', $1);
	lc($mois);
	$mois =~ s/[^a-z]+//i;
	my $adate = "$annee-".$mois{$mois}."-$jour";
	$mindate = $adate if (join('', split(/-/, $mindate)) > join('', split(/-/, $adate)));
	$maxdate = $adate if (join('', split(/-/, $maxdate)) < join('', split(/-/, $adate)));
    }
    if(/"([^"]+\/(projets|ta-commission|ta)\/[^"\-]+(|-a0).asp)"/ || /"(http:\/\/www.senat.fr\/leg[^\"]+)"/) { 
	$url = $1;
	if ($url !~ /^http/) {
	    $url = 'http://www.assemblee-nationale.fr'.$url;
	}
	$mindate = '' if ($mindate eq '99999999');
	my $pchambre = $chambre;
	if ($chambre eq 'CMP') {
	    if ($stade eq 'hemicycle') {
		if ($url =~ /senat/) {
		    $pchambre = "senat";
		}else{
		    $pchambre = 'assemblee';
		}
	    }elsif($stade eq 'depot') {
		$stade = 'commission';
	    }
	}
	push @steps, "$pchambre;$stade;$date;$mindate;$maxdate;$url" if ($stade);
#	print STDERR  "INFO: $pchambre;$stade;$date;$mindate;$maxdate;$url\n" if ($stade);
	$stade = '';
	$date = '';
	$mindate = '99999999';
	$maxdate = '';
    }
}

my $i = 0;
for(my $y = 0 ; $y <= $#{$procedure} ; $y++) {
    my $stepfound = 0;
    if ($steps[$i] =~ /$procedure->[$y][9];$procedure->[$y][10];/) {
	$stepfound = 1;
    }elsif ($steps[$i+1] =~ /$procedure->[$y][9];$procedure->[$y][10];/) {
	print STDERR "WARNING: Step missing : $steps[$i]\n";
	$i++;
	$stepfound = 1;
    }
    if ($stepfound) {
	my @step = split(/;/, $steps[$i]);
	$i++;
	if ($step[1] ne 'depot') {
	    if (!($procedure->[$y][13]) && $step[2]) {
		$procedure->[$y][13] = $step[2];
	    }
	    if (!($procedure->[$y][13]) && $step[3]) {
		$procedure->[$y][13] = $step[3];
	    }
	    if (!($procedure->[$y][14]) && $step[4]) {
		$procedure->[$y][14] = $step[4];
	    }
	    #If min date doesn't match the beginning one & if min date fits with the previous ones
	    if (($step[3] ne $procedure->[$y][13]) && (join('', split(/-/, $step[3])) >= join('', split(/-/, $procedure->[$y-1][14])))) {
		$procedure->[$y][13] = $step[3];
	    }

	    #if max date doesn't match the ending one & max date fits with the following one (if set)
	    if (($step[4] ne $procedure->[$y][14]) && (join('',split(/-/, $step[4])) >= join('',split(/-/,$procedure->[$y][13]))) &&  (!$procedure->[$y+1][13] || (join('',split(/-/, $step[4])) <= join('',split(/-/,$procedure->[$y+1][13]))))) {
		$procedure->[$y][14] = $step[4];
	    }
#	    my $diff = join('', split(/-/, $step[3])) - join('', split(/-/, $procedure->[$y][13]));
#	    print STDERR "WARNING: diff begin: $diff ($step[3] / ". $procedure->[$y][13]." / $step[2])".$procedure->[$y][8].";".$procedure->[$y][9].";".$procedure->[$y][10]."\n";
#	    
#	    $diff = join('', split(/-/, $step[4])) - join('', split(/-/, $procedure->[$y][14]));
#	    print STDERR "WARNING: diff end: $diff  ($step[4] / ". $procedure->[$y][14].")".$procedure->[$y][8].";".$procedure->[$y][9].";".$procedure->[$y][10]."\n";
	}
    }
    if (($procedure->[$y][10] eq 'depot') && $procedure->[$y][14]) {
	$procedure->[$y][13] = $procedure->[$y][14];
    }
    if (!($procedure->[$y][13]) && $procedure->[$y][14]) {
	print STDERR "WARNING: begining date missing ".$procedure->[$y][8].";".$procedure->[$y][9].";".$procedure->[$y][10]." => use ending date\n" unless ($procedure->[$y][13]);
	$procedure->[$y][13] = $procedure->[$y][14]
    }
    if ($y) {
	my $curbegdate = $procedure->[$y][13]; $curbegdate =~ s/-//g;
	my $prevenddate = $procedure->[$y-1][14]; $prevenddate =~ s/-//g;
	my $curenddate = $procedure->[$y][14]; $curenddate =~ s/-//g;
	print STDERR "WARNING: begining date ($curbegdate) should not later than the ending date ($curenddate) ".$procedure->[$y][8].";".$procedure->[$y][9].";".$procedure->[$y][10]."\n" if ($curbegdate > $curenddate && $curbegdate && $curenddate && ($procedure->[$y][6]+0));
	if ($curbegdate < $prevenddate && $curbegdate && $prevenddate && ($procedure->[$y][6]+0)) {
	    $procedure->[$y][13] = $procedure->[$y-1][14];
	    print STDERR "WARNING: begining date ($curbegdate) should not earlier than the ending date ($prevenddate) of the previous step ".$procedure->[$y][8].";".$procedure->[$y][9].";".$procedure->[$y][10]." => REWRITE IT\n";
	}
    }
}

for (my $y = $i ; $y <= $#steps ; $y++) {
    print "WARNING: step mission : ".$steps[$y]."\n";
}

for(my $y = 0 ; $y <= $#{$procedure} ; $y++) {
    print join(';', @{$procedure->[$y]})."\n";
}
