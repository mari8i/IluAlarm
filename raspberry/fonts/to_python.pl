#!/usr/bin/env perl
use strict;
use warnings;

my @in_files = split("\n", `find . -name "*.h"`);

foreach my $in_file (@in_files) {
    print "${in_file}\n";
    my $out_file = $in_file;
    $out_file =~ s/\.\/font_(.*)\.h/$1.py/;
    print "${out_file}\n";

    #"const unsigned char"

    open(my $fh, '>', $out_file) or die("Coudl not open ${out_file}");
    open(my $in, '<', $in_file)  or die("Coudl not open ${in_file}");

    my $where = 0;
    my $last_char = "";

    my @family = ();
    
    while (<$in>) {
	chomp();
	s/\r//;
	
	if (/const unsigned char (.*)\[/) {
	    my $font = $1;
	    print $fh "${font} = {\n";

	    push(@family, $font);
	    
	    $where = 1;
	}
	elsif ($where > 0) {
	    s/\/\//#/;
	    s/^\s*//;
	    if ($where == 3) {
		print $fh "    \"type\" : " . $_ . "\n";
	    }
	    elsif ($where == 4) {
		print $fh "    \"horizontal\" : " . $_ . "\n";
	    }
	    elsif ($where == 5) {
		print $fh "                                " . $_ . "\n";
	    }
	    elsif ($where == 8) {
		print $fh "    \"height\" : " . $_ . "\n";
		print $fh "    \"chars\" : (\n"
	    }
	    elsif (/\s*\/\*/) {
		$where = 10000;
	    }
	    
	    if ($where >= 10000) {		
		if (/^\};$/) {
		    $where = -1;
		    print $fh "    )\n";
		    print $fh "}\n\n\n";
		}
		else {
		    my $off = $where - 10000;
		    if ($off % 3 == 0) {
			s/.*character \d+ \"(.)\".*/$1/;
			$last_char = $_;
		    }
		    elsif ($off % 3 == 1) {
			s/,\s*$//;
			print $fh "        (" . $_ . "), # '${last_char}'\n";
		    }
		}
		
	    }

	    $where++;
	}

    }

    print $fh "Family = (" . join(", ", @family) . ")\n";
    
    close($fh);
    close($in);

}
