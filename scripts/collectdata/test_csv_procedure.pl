#!/usr/bin/perl
$old = 0;
while(<STDIN>) {
    @c = split /;/;
    $c[13]=~s/-//;
    $c[14]=~s/-//;
    next if ($c[6] eq 'XX');
    print "ERROR: previous\t $_" && exit 1 if ($c[13] < $old);
    print "ERROR: actual\t $_" && exit 1 if ($c[13] > $c[14]);
    $old = $c[14];
}
