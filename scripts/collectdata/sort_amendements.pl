#!/usr/bin/perl

$textjson = shift;
$outputtype = shift;

open JSON, "$textjson";
while(<JSON>) {
    next unless (/"article"/);
    if (/"order": (\d+), "titre": "([^"]+)"/) {
	$articles{$2} = $1 * 10;
    }
}
close JSON;

sub solveorder {
    $art = shift;
    $art =~ s/premier/1er/i;
    $art =~ s/unique/1er/i;
    if ($art =~ /article (\d.*)/i) {
	$order = $articles{$1};
	if ($art =~ /avant/) {
	    $order--;
	}elsif ($art =~ /après/) {
	    $order++;
	}
    }
    return $order;
}

while(<STDIN>) {
    if ($outputtype eq 'csv'){
	@csv = split /;/;
	$order = solveorder($csv[4]);
	$order = 'article order' if ($csv[4] eq "sujet");
	s/;$csv[4];/;$order;$csv[4];/;
    }elsif($outputtype eq 'xml') {
	if (/<sujet>([^<]+)<\/sujet>/) {
	    $sujet = $1;
	    $order = solveorder($1);
	    s/<sujet>$sujet<\/sujet>/<article_order>$order<\/article_order><sujet>$sujet<\/sujet>/;
	}
    }elsif($outputtype eq 'json') {
	if (/"sujet":"([^"]+)"/) {
	    $sujet = $1;
	    $order = solveorder($sujet);
	    s/"sujet":"$sujet",/"sujet":"$sujet","article_order":$order,/;
	}
    }
    print;
}
