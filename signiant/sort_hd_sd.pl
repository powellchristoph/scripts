#!dds_perl

%script_lib_obj:SolutionStandardHeaderPerl%
%script_lib_obj:SolutionModifyInputValue%
%script_lib_obj:SolutionSigListXML%
%script_lib_obj:SolutionGetUtf8String%
%script_lib_obj:SolutionSplitPaths%

require File::Path;
use File::Basename;
#use Data::Dumper;
use File::Copy;

my $SUPERDEBUG=FALSE;
my $mediainfoCmd = '/usr/bin/mediainfo';
my $logfile = "/var/log/signiant/%job_name%.log";


# File list
my %originalMetaHash;
my %SourceBasePathHash;
my @FileList;
my @FileSize;
my @FileType;
my $SDPath;
my $HDPath;
my $FileListXML;

# Outputs
my $ReturnCode;
my $ReturnMessage;
my @TransferredFiles;
my @FailedFiles;
my $TransferredFileCount;
my $FailedFileCount;

# Miscellaneous
my $XMLPathListType;
my $SigListXattrs;
my @ElArray;
my $FileErrors;
my $IsLinux;

# File List Assignment
$FileListXML = <<'__fileList__';
%Inputs.fileList%
__fileList__
$FileListXML = GetUtf8String(ModifyInputValue($FileListXML,0));

# Path assignments
$SDPath= "%Inputs.sDTarget%";
$HDPath= "%Inputs.hDTarget%";

# Open log file
if ( ! open LOG, ">> $logfile")
{
    SigPrintLog( "The log file $logfile, cannot be opened.", LOGERROR );
    SetOutputs();
    exit(1);
}

# Check that path exists
if ( ! -d $SDPath || ! -d $HDPath) 
{
    # Path doesn't exist
    SigPrintLog( "The SDPath or HDPath does not exist.", LOGERROR );
    SetOutputs();
    exit(1);
}
  
# Check for valid input and acutal data
if (IsSigListXmlFormat($FileListXML) && !FileListXMLContainsData())
{
    SigPrintLog( "No files passed as input, exiting component", LOGINFO );
    SetOutputs();
    exit(0);
}

# Parse the File List input
if ( !GetFiles() )
{
    $ReturnCode = 1;
    $ReturnMessage = "Invalid input specified.";
    SetOutputs();
    exit(1);
}

# Only using height for this check
my $height;
my $timestamp;

foreach my $file (@FileList)
{
    if (-f $file) 
    {
        $height = `$mediainfoCmd "$file" --Inform="Video;%Height%"`;
        
        $timestamp = localtime(time);
        
        if ($height > 486) 
        {
            # HD File
            SigPrintLog("move($file, $HDPath)", LOGDEBUG);
            move($file, $HDPath)
                or die(SigPrintLog("move($file, $HDPath) $!",LOGERROR));
            print LOG "$timestamp: $file moved to $HDPath\n";
        } elsif ($height > 0 && $height < 486) 
        {
            # SD File
            SigPrintLog("move($file, $SDPath)", LOGDEBUG);
            move($file, $SDPath)
                or die(SigPrintLog("move($file, $SDPath) $!",LOGERROR));
            print LOG "$timestamp: $file moved to $HDPath\n";
        } else 
        {
                    SigPrintLog("$file is not a media file, ignoring.", LOGINFO);
                    print LOG "$timestamp: $file is not a media file, ignoring...\n";
        }
    }
}

close LOG;
exit(0);

sub FileListXMLContainsData
{
    if (IsSigListXmlFormat($FileListXML))
    {
        if ( SigListXMLParse( $FileListXML, \$XMLPathListType, \@ElArray, \$SigListXattrs ) != 0 )
        {
            return(FALSE);
        }
        else
        {
            for (my $i=0; $i < scalar @ElArray; $i++)
            {
                if ($ElArray[$i]{'V'} ne "")
                {
                    return(TRUE);
                }

            }
        }
    }

    return(FALSE);
}

sub GetFiles
{
    my $i;
    my $size;
    my @SourcePathArray = ();

    # Break down file list
    if ( IsSigListXmlFormat($FileListXML) )
    {
        # SourceData is in SigList XML format...
        if ( SigListXMLParse( $FileListXML, \$XMLPathListType, \@ElArray, \$SigListXattrs ) != 0 )
        {
            $ReturnMessage = "%job_template% failed: File List XML specification is not parsable";
            return ($FALSE);
        }
        else
        {
            @FileList = SigListGetELementsByAttribute( \@ElArray, "V" );
        }

        if (uc($XMLPathListType) eq "FILEDIR")
        {
            @SourcePathArray = SigListGetELementsByAttribute(\@ElArray, "V");
        }
        else    ## PATHLIST
        {
            @SourcePathArray = SolutionSplitPaths($SigListXattrs, ',');
        }

        # Turn ElArray into hash based on the V attribute
        my $size = scalar @ElArray;

        for ( my $i = 0 ; $i < $size ; $i++ )
        {
            # We only care about files
            if ((uc($ElArray[$i]{'T'}) eq 'F') || ($ElArray[$i]{'T'} eq ''))
            {
                $originalMetaHash{ $ElArray[$i]{'V'} } = {
                    'T'  => $ElArray[$i]{'T'},
                    'S'  => $ElArray[$i]{'S'},
                    'V'  => $ElArray[$i]{'V'},
                    'MD' => $ElArray[$i]{'MD'},
                    'CT' => $ElArray[$i]{'CT'},
                    'IT' => $ElArray[$i]{'IT'},
                    'AT' => $ElArray[$i]{'AT'},
                    'MT' => $ElArray[$i]{'MT'}
                };
            }
        }
    }
    else
    {
        # SourceData is in legacy format...
        @FileList = SolutionSplitPaths( $FileListXML, ',' );

        my $size = scalar @FileList;

        # Make up metadata - assume it's a file and set the size to '0'
        for ( my $i = 0 ; $i < $size ; $i++ )
        {
            $originalMetaHash{ $FileList[$i] } = {
                'T'  => '',
                'S'  => '0',
                'V'  => $FileList[$i],
                'MD' => '',
                'CT' => '',
                'IT' => '',
                'AT' => '',
                'MT' => ''
            };
        }

        @SourcePathArray = @FileList;
    }

    #
    # Build the hash of base source paths to be used for stripping from the filename on the target system...
    #
    foreach my $sourcePath (@SourcePathArray) {
        my $searchKey = lc(ModifyInputValue($sourcePath,0));
        $searchKey =~ s|\\|/|g; ## convert all '\' chars to '/' to simplify REs for path parsing/matching
        $SourceBasePathHash{$searchKey} = $searchKey;
    }
    
    return ($TRUE);
}
