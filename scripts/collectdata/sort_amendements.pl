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
        $order = 'article order' if ($csv[4] eq "sujet");
        s/;$csv[4];/;$order;$sujet;/;
    } elsif($outputtype eq 'xml') {
        if (/<sujet>([^<]+)<\/sujet>/) {
            $sujet = clean_subject($1);
            $order = solveorder($1);
            s/<sujet>[^<]*<\/sujet>/<article_order>$order<\/article_order><sujet>$sujet<\/sujet>/;
        }
    } elsif($outputtype eq 'json') {
### !!! WARNING NE MARCHE PAS AVEC LES JSON EN UNE LIGNE QUE SERVENT ND/NS, UN SEUL ORDRE RETROUVÉ !!!
        if (/"sujet":"([^"]+)"/) {
            $sujet = clean_subject($1);
            $order = solveorder($sujet);
            s/"sujet":"[^"]*",/"sujet":"$sujet","article_order":$order,/;
        }
    }
    print;
}
