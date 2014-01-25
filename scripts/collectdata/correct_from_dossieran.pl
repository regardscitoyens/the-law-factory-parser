#!/usr/bin/perl

use WWW::Mechanize;
use utf8;

@row = split(/;/, <STDIN>);
$legislature = 14;
if ($row[0] lt "2012-06-29") {
  $legislature = 13;
}
$url = "http://www.assemblee-nationale.fr/$legislature/dossiers/".$row[3].".asp";
$a = WWW::Mechanize->new();
$a->get($url);
$content = $a->content;
utf8::encode($content);
%mois = ('janvier'=>'01', 'fvrier'=>'02', 'mars'=>'03', 'avril'=>'04', 'mai'=>'05', 'juin'=>'06', 'juillet'=>'07', 'aot'=>'08', 'septembre'=>'09','octobre'=>'10','novembre'=>'11','dcembre'=>'12');
@steps = ();
foreach (split(/\n/, $content)) {
    if (s/.*<a name="ETAPE[^"]+">((<a[^>]+>|<i>|<\/i>|<br\/?>|<\/a>|<sup>|<\/sup>|<\/font>|<\/b>|[^>])+)<\/p>(.*)//) {
	$section = $1;
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
    }elsif(!/nomm..? |nomination/i && / (\d+) (janvier|f..?vrier|mars|avril|mai|juin|juillet|ao..?t|septembre|octobre|novembre|d..?cembre) (\d+)/ && $chambre && $stade && !$date) {
	$annee = $3; $mois = $2; $jour = $1;
	lc($mois);
	$mois =~ s/[^a-z]+//i;
	$date = "$annee-".$mois{$mois}."-$jour";
    }
    if(/"([^"]+\/(projets|ta-commission|ta)\/[^"\-]+(|-a0).asp)"/) {
	$url = $1;
	if ($url !~ /^http/) {
	    $url = 'http://www.assemblee-nationale.fr'.$url;
	}
	push @steps, "$chambre;$stade;$date;$url" if ($chambre eq 'assemblee');
	$stade = '';
	$date = '';
    }
}
$i = 0;
while ($#row > 9) {
    if ($steps[$i] =~ /$row[8];$row[9]/) {
	@step = split(/;/, $steps[$i]);
	print STDERR "WARNING: AN url differs on $chambre $stade (original: $row[10] ; new: $step[3])\n" if ($row[10] ne $step[3]);
	$row[10] = $step[3];
	$row[12] = $step[2];
	$i++;
    }
    print STDERR "WARNING: begining date missing $row[7];$row[8];$row[9]\n" unless ($row[12]);
    print join(';', @row);
    @row = split(/;/, <STDIN>);
}
