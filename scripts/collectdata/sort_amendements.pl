#!/usr/bin/perl

$textjson = shift;
$outputtype = shift;

open JSON, "$textjson";
while(<JSON>) {
    next unless (/"article"/);
    if (/"order": (\d+),.*"titre": "([^"]+)"/) {
        $articles{$2} = $1 * 10;
    }
}
close JSON;

sub clean_subject {
    $subj = shift;
    $subj =~ s/art(\.|icle|\s)*(\d+)/article \2/i;
    $subj =~ s/\(.*//;
    $subj = lc($subj);
    return $subj;
}
sub solveorder {
    $art = shift;
    $art =~ s/premier/1er/i;
    $art =~ s/unique/1er/i;
    if ($art =~ /article (\d.*)/i) {
        $order = $articles{$1};
        if ($art =~ /avant/) {
            $order--;
        } elsif ($art =~ /apr[eè]s/) {
            $order++;
        }
    }
    if (!$order) {
        $order = -1;
    }
    return $order;
}

while(<STDIN>) {
    if ($outputtype eq 'csv'){
        @csv = split /;/;
        $sujet = clean_subject($csv[4]);
        $order = solveorder($csv[4]);
        $order = 'ordre article' if ($csv[4] eq "sujet");
        s/;$csv[4];/;$order;$sujet;/;
    } elsif($outputtype eq 'xml') {
	@partialxml = ();
	foreach $l (split/<amendement>/) {
	    if ($l =~ /<sujet>([^<]+)<\/sujet>/) {
		$sujet = clean_subject($1);
		$order = solveorder($1);
		$l =~ s/<sujet>[^<]*<\/sujet>/<ordre_article>$order<\/ordre_article><sujet>$sujet<\/sujet>/;
	    }
	    push @partialxml, $l;
	}
	$_ = join('<amendement>', @partialxml);
    } elsif($outputtype eq 'json') {
	@partialjson = ();
	foreach $l (split(/},/)) {
	    if ($l =~ /"sujet":"([^"]+)"/) {
		$sujet = clean_subject($1);
		$order = solveorder($sujet);
		$l =~ s/"sujet":"[^"]*",/"sujet":"$sujet","ordre_article":$order,/;
	    }
	    push @partialjson, $l;
	}
	$_ = join('},', @partialjson);
    }
    print;
}
