#!/usr/bin/perl

$textjson = shift;
$outputtype = shift;

open JSON, "$textjson";
while(<JSON>) {
    next unless (/"article"/);
    if (/"titre": "([^"]+)"/) {
        $titre = $1;
        /order": (\d+),/;
        $articles{lc($titre)} = $1 * 10;
    }
}
close JSON;

sub clean_subject {
    $subj = shift;
    $subj = lc($subj);
    $subj =~ s/\\u00c8/\\u00e8/ig;
    $subj =~ s/È/è/g;
    $subj =~ s/ (prem)?ier/ 1er/i;
    $subj =~ s/unique/1er/i;
    $subj =~ s/\s*\(((avant|apr).*)\)/ \1/;
    $subj =~ s/\s*\(.*$//i;
    $subj =~ s/\s*$//;
    $subj =~ s/^\s*//;
    $subj =~ s/^(\d)/article \1/;
    $subj =~ s/articles/article/i;
    $subj =~ s/art(\.|icle|\s)*(\d+)/article \2/i;
    $subj =~ s/^(apr\S+s|avant)\s*/article additionnel \1 /;
    $subj =~ s/(apr\S+s|avant)\s+Article/\1 l'article/i;
    $subj =~ s/(\d+e?r? )([a-z]{1,2})$/\1\U\2/i;
    $subj =~ s/(\d+e?r? \S+ )([a-z]+)$/\1\U\2/i;
    $subj =~ s/ annexe.*//i;
    $subj =~ s/ rapport.*//i;
    $subj =~ s/article 1$/article 1er/i;
    return $subj;
}
sub solveorder {
    $art = shift;
    $order = 10000;
    if ($art =~ /^titre$/i || $art =~ /^intitul/i) {
        return 0;
    } elsif ($art =~ /^motion/i) {
        return 1;
    } elsif ($art =~ /^(pro(jet|position)|texte)/i) {
        return 5;
    } elsif ($art =~ /article (1er.*|(\d+).*)$/i) {
        if ($articles{lc($1)}) {
            $order = $articles{lc($1)};
        } elsif ($articles{$2}) {
            $order = $articles{$2};
        }
        if ($art =~ /avant/i) {
            $order--;
        } elsif ($art =~ /apr\S+s/i) {
            $order++;
        }
    }
    return $order;
}

while(<STDIN>) {
    if ($outputtype eq 'csv'){
        @csv = split /;/;
        $sujet = clean_subject($csv[6]);
        $order = solveorder($sujet);
        $order = 'ordre article' if ($sujet eq "sujet");
        $csv[6] =~ s/([()[\]+.?*{}])/\\\1/g;
        s/;$csv[6];/;$order;$sujet;/;
    } elsif($outputtype eq 'xml') {
	@partialxml = ();
	foreach $l (split /<amendement>/) {
	    if ($l =~ /<sujet>([^<]+)<\/sujet>/) {
		$sujet = clean_subject($1);
		$order = solveorder($sujet);
		$l =~ s/<sujet>[^<]*<\/sujet>/<ordre_article>$order<\/ordre_article><sujet>$sujet<\/sujet>/;
	    }
	    push @partialxml, $l;
	}
	$_ = join('<amendement>', @partialxml);
    } elsif($outputtype eq 'json') {
	@partialjson = ();
	foreach $l (split /},{"amendement":{/) {
	    if ($l =~ /"sujet":"([^"]+)"/) {
		$sujet = clean_subject($1);
		$order = solveorder($sujet);
		$l =~ s/"sujet":"[^"]*",/"sujet":"$sujet","ordre_article":$order,/;
	    }
	    push @partialjson, $l;
	}
	$_ = join('},{"amendement":{', @partialjson);
    }
    print;
}
