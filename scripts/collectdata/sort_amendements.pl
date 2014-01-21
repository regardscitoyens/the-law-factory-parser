#!/usr/bin/perl

$textjson = shift;
$outputtype = shift;

open JSON, "$textjson";
while(<JSON>) {
    next unless (/"article"/);
    if (/"order": (\d+),.*"titre": "([^"]+)"/) {
        $articles{lc($2)} = $1 * 10;
    }
}
close JSON;

sub clean_subject {
    $subj = lc(shift);
    $subj =~ s/\s*\(((avant|apr).*)\)/ \1/;
    $subj =~ s/\(.*//;
    $subj =~ s/\s*$//;
    $subj =~ s/^\s*//;
    $subj =~ s/^(\d)/Article \1/;
    $subj =~ s/articles/Article/i;
    $subj =~ s/art(\.|icle|\s)*(\d+)/Article \2/i;
    $subj =~ s/^(apr\S+s|avant)\s*/Article additionnel \1 /;
    $subj =~ s/(apr\S+s|avant)\s+Article/\1 l'article/i;
    $subj =~ s/^(.)/\U\1/;
    $subj =~ s/(\d+e?r? )([a-z]{1,2})$/\1\U\2/i;
    $subj =~ s/(\d+e?r? \S+ )([a-z]+)$/\1\U\2/i;
    return $subj;
}
sub solveorder {
    $art = shift;
    if ($art =~ /^motion/i) {
        return 0;
    } elsif ($art =~ /^(pro(jet|position)|texte)/i) {
        return 1;
    } elsif ($art =~ /^titre$/i || $art =~ /^intitul/i) {
        return -5;
    }
    $art =~ s/premier/1er/i;
    $art =~ s/unique/1er/i;
    if ($art =~ /article (\d.*)/i) {
        $order = $articles{lc($1)};
        if ($art =~ /avant/i) {
            $order--;
        } elsif ($art =~ /apr\S+s/i) {
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
