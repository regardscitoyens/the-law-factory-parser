#!/usr/bin/perl
$old = 0;
while(<STDIN>) {
    @c = split /;/;
    $c[13]=~s/-//g;
    $c[14]=~s/-//g;
    next if ($c[6] eq 'XX');
    print "ERROR: previous\t $_" && exit 1 if ($c[13] < $old);
    print "ERROR: actual\t $_" && exit 1 if ($c[13] > $c[14]);
    print STDERR "INFO: \t $c[13] -> $c[14]\n";
    $old = $c[14];
}
