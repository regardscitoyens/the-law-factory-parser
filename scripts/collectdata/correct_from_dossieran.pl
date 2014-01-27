#!/usr/bin/perl

use WWW::Mechanize;
use utf8;

@row = split(/;/, <STDIN>);
if (!$row[4] || !$row[3]) {
  print STDERR "WARNING: no dossier AN found, skipping corrector\n";
  while ($#row > 10) {
    print join(';', @row);
    @row = split(/;/, <STDIN>);
  }
  exit(0);
}

$url = "http://www.assemblee-nationale.fr/$row[3]/dossiers/".$row[4].".asp";
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
while ($#row > 10) {
    if ($steps[$i] =~ /$row[9];$row[10]/) {
	@step = split(/;/, $steps[$i]);
	print STDERR "WARNING: AN url differs on $chambre $stade (from Senat: $row[11] ; from AN: $step[3])\n" if ($row[11] ne $step[3]);
#   Keep warnings but don't rewrite urls since Senate rebuilt data is most of the times better than AN's
#	$row[11] = $step[3];
	$row[13] = $step[2];
	$i++;
    }
    print STDERR "WARNING: begining date missing $row[8];$row[9];$row[10]\n" unless ($row[13]);
    print join(';', @row);
    @row = split(/;/, <STDIN>);
}
