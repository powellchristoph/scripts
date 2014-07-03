#!/usr/bin/perl
use File::Basename;


# File Extensions

my @FileList = qw(file.txt file.TAR file.tar file.zip file.ZIP);

my $isZipped = false;

my @exts = qw(.tar .TAR .xml .XML .zip .ZIP .jpeg .JPEG .jpg .JPG .bmp .BMP);

foreach my $file (@FileList)
{
    print $file . "\n";
        my ($dir, $name, $ext) = fileparse($file, @exts);
        
        #SigPrintLog("Ext: $ext", LOGINFO);

        #XML
        if ($ext =~ /\.xml/i )
        {

            print "Found xml\n";
            #SigPrintLog("Found xml: $file", LOGINFO);
        }
        elsif ($ext =~  /\.jpeg|\.jpg|\.bmp/i)
        {
            print "Found art\n";
            #SigPrintLog("Found artwork: $file", LOGINFO);
        }
        elsif ($ext =~ /\.zip/i && $isZipped)
        {
            print "Found zipped\n";
            #SigPrintLog("Found zipped artwork: $file", LOGINFO);
        }
        elsif ($ext =~ /\.tar/i )
        {
            print "Found tar\n";
            #SigPrintLog("Found media: $file", LOGINFO);
        }
        else
        {
            print "Found unknown.\n";
            #SigPrintLog("Found unknown file: $file", LOGINFO);
        }
}
