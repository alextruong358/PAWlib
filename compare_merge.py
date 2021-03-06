#!/usr/bin/env python

from __future__ import division
import os
import sys
import commands
import glob



def read_data(filename):
        """reads in data from file, creates list of list, returns list of list and headers"""

        data = []
        headers = []
        with open(filename, 'r') as f:
                for line in f:
                        if line.startswith('#'):
                                headers.append(line.strip())
                                continue
                        else:
                                data.append(line.strip())


        data = [line.split('\t') for line in data]


        return headers, data


def compare(ref_data, query_data, file_name):
        """first compares chr#, position, and ref; then, compares alt to determine if match"""

        query_out_data = []
        ref_out_data = []
        multiallelic_locations = []

        lquery_data = query_data
        lref_data = ref_data

        #makes an array of all the alternate alleles from the reference and query data
        ref_alt_key = [i[4] for i in lref_data]
        query_alt_key = [i[4] for i in lquery_data]

        #makes an array of Chr#, position, and refrence allele for both reference and query data
        ref_data_key = [tuple((i[0], i[1], i[3])) for i in lref_data]
        query_data_key = [tuple((i[0], i[1], i[3])) for i in lquery_data]

        #find the set intersection of the reference and query data key
        common = set(ref_data_key).intersection( set(query_data_key) )

        #goes through each common variant
        for i in common:
                ref_index = ref_data_key.index(i)
                query_index = query_data_key.index(i)

                #for the common variants, if the alt matches exactly, append each to a list
                if query_alt_key[query_index] == ref_alt_key[ref_index]:
                        query_out_data.append(query_data[query_index])
                        ref_out_data.append(ref_data[ref_index])
                #if no exact match, split on the comma, and check if any of the alleles match between ref and alt
                else:
                        query_temp = query_alt_key[query_index].split(',')
                        ref_temp = ref_alt_key[ref_index].split(',')

                        if any(j in query_temp for j in ref_temp):
                                query_out_data.append(query_data[query_index])
                                ref_out_data.append(ref_data[ref_index])
                                multiallelic_locations.append(query_data_key[query_index])
        
        return query_out_data, ref_out_data, multiallelic_locations


def write_to_file(ref_file, query_file, ref_headers, query_headers, query_out_data, ref_out_data, multiallelic_locations):
        """standard write to file, no trailing tabs, could be done with writelines and join"""
        
        #appends shared.vcf to the end of each file
        new_ref_file = ref_file[0:-4] + '_shared.vcf'
        new_query_file = query_file[0:-4] + '_shared.vcf'

        with open(new_ref_file, 'w') as w:
                for line in ref_headers:
                        w.write(line + '\n')

                for row in ref_out_data:
                        for index, column in enumerate(row):
                                if index != len(row) - 1:
                                        w.write('%s\t' % column)
                                else:
                                        w.write('%s\n' % column)

        with open(new_query_file, 'w') as w:
                for line in query_headers:
                        w.write(line + '\n')

                for row in query_out_data:
                        for index, column in enumerate(row):
                                if index != len(row) - 1:
                                        w.write('%s\t' % column)
                                else:
                                        w.write('%s\n' % column)


        hold = new_ref_file.split('_')[0:2]
        wobblefile = hold[0] + '_' + hold[1]

        #prints the variant information for the multiallelic sites for reference
        with open('%s_incomplete_match_coordinates.txt' % wobblefile, 'w') as w:
                for line in multiallelic_locations:
                        w.write(str(line) + '\n')


def findbcf():

        #this function finds the bcftools executable
        print 'Locating bcftools installation...'

        find_bcftools_path = commands.getstatusoutput('find ~/ -name bcftools -executable -type f -print 2>/dev/null')

        bcfdir = find_bcftools_path[1]

        print 'Done!'

        return bcfdir


def bcfmerge(rna, wes, bcfdir):
        """bgzip and tabix output files from gsearch, and use bcftools to merge matching files"""

        rnatemp = rna[0:-4] + '_sorted.vcf'
        westemp = wes[0:-4] + '_sorted.vcf'

        rnatabix = rnatemp + '.gz'
        westabix = westemp + '.gz'
        
        bgzipcommand = "bgzip %s; bgzip %s" % (rnatemp, westemp)

        tabixcommand = "tabix -p vcf %s; tabix -p vcf %s" % (rnatabix, westabix)

        sortcommand = 'vcf-sort %s > %s; vcf-sort %s > %s' % (rna, rnatemp, wes, westemp)
        
        #sorts the vcf, bgzips it, and then tabixes it
        os.system(sortcommand)

        #print 'bgzipping gsearch output files...'
        os.system(bgzipcommand)
        #print 'Done!'
        #print '-----------------------------------------------'
        #print 'Indexing with tabix...'
        os.system(tabixcommand)
        #print 'Done!'
        #print '-----------------------------------------------'

        mergename = rna.split('_')[0] + '_' + rna.split('_')[1] + '_' + rna.split('_')[2] + '_WES_' + rna.split('_')[3] + '_' + rna.split('_')[4][0:-4]+ '_sorted_merged.vcf'

        mergecommand = '%s merge -O v %s %s > %s' % (bcfdir, rnatabix, westabix, mergename)

        #print 'Merging gsearch output files...'
        os.system(mergecommand)
        #print 'Done!'

        #print '-----------------------------------------------'
        
        return

def main():

        #all o fthe RNA and WES files
        RNA_files = glob.glob('*_RNA_snp.vcf')
        WES_files = glob.glob('*_WES_snp.vcf')

        #simple check to see that there are an equal number of RNA and WES files, this can be commented out
        if len(RNA_files) != len(WES_files):
                print 'Missing files'
                sys.exit(1)
        
        #simple command line progress tracker
        counter = 0
        print 'Processing file comparisons...'
        sys.stdout.write('Progress: 0% \r')
        sys.stdout.flush()
        for rna_name in RNA_files:
                for wes_name in WES_files:
                        if rna_name.split('-')[0] == wes_name.split('-')[0]:
                                ref_file = rna_name
                                query_file = wes_name

                                ref_headers, ref_data = read_data(ref_file)
                                query_headers, query_data = read_data(query_file)

                                query_out_data, ref_out_data, multiallelic_locations = compare(ref_data, query_data, ref_file)
                                write_to_file(ref_file, query_file, ref_headers, query_headers, query_out_data, ref_out_data, multiallelic_locations)

                counter += 1
                progress = counter / len(RNA_files) * 100

                if progress != 100:
                        sys.stdout.write('Progress: %d%%   \r' % progress)
                        sys.stdout.flush()
                else:
                        sys.stdout.write('Progress: 100%\n')
                        print 'Done!'

        print '----------------------------------------------------'

        bcfdir = findbcf()
        
        #takes the two half files and uses bcftools to merge

        rnapool = glob.glob('*_RNA_snp_shared.vcf')
        wespool = glob.glob('*_WES_snp_shared.vcf')

        counter = 0
        print 'Merging matching files...'
        sys.stdout.write('Progress: 0% \r')
        sys.stdout.flush()
        for rna in rnapool:
                for wes in wespool:
                        if rna.split('-')[0] == wes.split('-')[0]:
                                rna_match = rna
                                wes_match = wes

                                bcfmerge(rna, wes, bcfdir)

                counter += 1
                progress = counter / len(rnapool) * 100

                if progress != 100:
                        sys.stdout.write('Progress: %d%%   \r' % progress)
                        sys.stdout.flush()
                else:
                        sys.stdout.write('Progress: 100%\n')
                        print 'Done!'

        #outdir = makefolder()

        #print 'Organizing files...'

        #os.system('cd ' + outdir + '; mkdir matching; mv output1.vcf matching; mv output2.vcf matching; mkdir nonmatching; mv unmatched.output1.vcf nonmatching; mv unmatched.output2.vcf nonmatching; mkdir merged')

        #removes temporary files
        gz_tbi_files = glob.glob('*.gz*')
        merge_halves = glob.glob('*_shared.vcf')
        temp_files = gz_tbi_files + merge_halves
        print "Deleting temporary gz/tbi files..."
        
        for temp_file in temp_files:
                os.system('rm %s' % temp_file)
                
        
        print "Done!"
        
        print 'Complete!'



if __name__ == "__main__":
        main()



