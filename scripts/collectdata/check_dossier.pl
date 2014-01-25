#!/usr/bin/perl

$id = shift;

if (!$id) {
	print "USAGE perl parse_dossier.pl <url senat> | perl check_dossier.pl <url senat>\n";
	print "\n";
	print "Vérifie qu'un CSV produit par parse_dossier.pl est bien formé\n";
	print "L'argument passé ne sert qu'à identifier l'url à l'origine du CSV\n";
	exit 1;
}

@data = ('INIT');
@extra = ();
@etapes = ();
$errors = 0;
while(<STDIN>) {
    chomp;
    @csv = split(/;/);
    if (!$data[$csv[6]]) {
	$data[$csv[6]] = $csv[8];
    $extra[$csv[6]] = $csv[10];
    $etapes[$csv[6]] = $csv[7];
    }elsif ($data[$csv[6]-1] ne 'CMP' && $csv[6] ne 'EXTRA') {
	print STDERR "WARNING: $id: duplicated entry ".$csv[6]."\n";
    }
  if ($csv[10] ne "texte retire" && $csv[10] ne "renvoi en commission") {
    if ($csv[10] !~ /^http/ && $csv[6] ne 'EXTRA') {
	print "$id: not valid url ".$csv[10]."\n";
	$errors++;
    }elsif($csv[8] =~ /assemblee|senat/ && $csv[10] !~ /$csv[8]/) {
	print "$id: not a chambre url ".$csv[10]."\n";
	$errors++;
    }
  }
}

for ($i = 0 ; $i < $#data ; $i++) {
    unless($data[$i]) {
	if ($data[$i+1] ne 'CMP' &&
     $etapes[$i-1] ne "l. définitive" &&
     !($etapes[$i+1] eq 'nouv. lect.' && $data[$i-1] eq "CMP") &&
     $extra[$i+1] ne 'texte retire' &&
     $extra[$i+1] ne 'renvoi en commission') {
	    print "$id: missing step $i\n" ;
	    $errors++;
	}
    }
}

exit $errors;

