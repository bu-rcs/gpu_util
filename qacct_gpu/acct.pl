#!/usr/bin/perl
use strict;
use Time::Local;

sub usage {
    print stderr "usage: $0 [-s] start end\n";
    print stderr "\tdate format: MM/DD/YY\n";
    exit 1;
}

my $acctfile = "/usr/local/sge/sge_root/default/common/accounting";

my $hash = "#";
my $Start = 0;
my $End = 0;
my $summary = 0;
my $short = 0;
my %stats = ();

if ($ARGV[0] eq "-o") {
    $acctfile = "/usr/local/sge/sge_root/ood/common/accounting";
    shift @ARGV;
}

if ($ARGV[0] eq "-s") {
    $summary = 1;
    shift @ARGV;
}

if ($ARGV[0] eq "-short") {
    $summary = 1;
    $short = 1;
    shift @ARGV;
}

if ($#ARGV == 1) {
    $Start = &parse_date($ARGV[0]);
    $End   = &parse_date($ARGV[1]);
}
elsif ($#ARGV == 0) {
    $Start = &parse_date($ARGV[0]);
    $End   = $Start;
}
elsif ($#ARGV == -1) {
    chomp(my $today = `date '+%m/%d/%y'`);
    $Start = &parse_date($today);
    $End   = $Start;
} else {
    usage;
}
usage if (($Start == 0) || ($End == 0) || ($Start > $End));

# make this the end of the day
$End += 24*60*60 - 1;
my $now = time;
$End = $now if ($End > $now);

open(ACCT, $acctfile) or die "can't open $acctfile: $!";
my $distance = int((stat ACCT)[7] / 2);
my $min = 1024000;

while ($distance > $min) {
    my $prevpos = tell(ACCT);
    seek(ACCT, $distance, 1);
    # find next record
    my $buf; do {read(ACCT, $buf, 1)} until ($buf eq "\n");
    my $line = <ACCT>;
    my $end_time = (split ':', $line)[10];
    #print "$prevpos $end_time $Start\n";

    if ($end_time >= $Start) {
	#too far
	seek(ACCT, $prevpos, 0);
    }
    $distance = int($distance / 2);
}
my $prev_end_time = 0;
my $printtime = $Start + 3600;

while (<ACCT>) {
    next if (/^$hash/);
    my ($queue, $host, $group, $user, $name, $job_id, $account, $priority,
        $sub_time, $start_time, $end_time, $failed, $exit_status,
        $granted_pe, $slots, $task,
	$mem,
	$io,
	$category,
	$pe_task_id,
	$maxvmem
	) = (split ':')[0..12,33,34,35,37,38,39,41,42];

    my $slave = 0;
   if ($end_time) {
	$prev_end_time = $end_time;
	next if ($end_time < $Start);
    } else {
	$end_time = $prev_end_time;
	$slave = 1;
    }

    last if ($end_time > $End);

    $host =~ s/\..*$//;

    if ($summary) {
	if (!$slave) {
	    $stats{$user}->{jobs}  += 1;
	    $stats{$user}->{slots} += $slots;
	    $stats{$user}->{rt} += $end_time - $start_time;
	    push @{$stats{$user}->{times}} , $end_time - $start_time;
	}
	if ($end_time > $printtime) {
	    print_summary($end_time);
	    %stats = ();
	    $printtime += 3600;
	}
    } else {
	printf "%7d.%d %8s %8s %10s %3d |%7.1f |%s %6.2f %6.2f | %3d %3d | %22s | %s | %s\n",
	    $job_id, $task,
	    $user,
	    $group,
	    $host,
	    $slots,
	    $maxvmem / (1024*1024*1024),
	    &format_date($end_time),
	    ($end_time - $start_time) / 3600,
	    ($start_time - $sub_time) / 3600,
	    $exit_status,
	    $failed,
	    $granted_pe,
	    $category,
	    $name;
    }
}
close(ACCT);

print_summary() if $summary;

####
sub parse_date {
    my ($mm, $dd, $yy) = split("/", $_[0], 3);
    $mm = int($mm);
    $dd = int($dd);
    $yy = int($yy);
        if (($mm >= 1) && ($mm <= 12) &&
	            ($dd >= 1) && ($dd <= 31) &&
	    ($yy >= 0) && ($yy <= 99)) {
	    return timelocal(0, 0, 0, $dd, $mm - 1, $yy + 2000);
	}
    return 0;
}

sub format_date {
    my ($min,$hour,$mday,$mon,$year) = (localtime($_[0]))[1,2,3,4,5];
    return sprintf("%02d:%02d %02d/%02d/%02d", $hour, $min, $mon + 1, $mday, $year - 100);
}

sub print_summary {
    my $time = $_[0] ? $_[0] : time;
    print scalar localtime($time), "\n";
    for my $user (sort keys %stats) {
	my $med = 0;
	my $jobs = $stats{$user}->{jobs};
	my @times = sort { $a <=> $b} @{$stats{$user}->{times}};
	if ($jobs % 2 == 1) {
	    $med = $times[($jobs - 1) / 2];
	} else {
	    $med = ($times[($jobs - 2) / 2] + $times[$jobs / 2]) / 2;
	}

	next if ($short && $med > 180);

	printf "%8s  %6d  %6d  %9.2f  %9.2f\n",
	$user,
	$jobs,
	$stats{$user}->{slots},
       	$stats{$user}->{rt} / $jobs / 60,
	$med / 60;
    }
}
