#!/usr/bin/env python


from __future__ import division
import os
import sys



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
        
        #This line makes data a list of lists for simpler indexing    
        data = [line.split('\t') for line in data]


        return headers, data


def filter_qual_WES(data, input_qual, input_het, input_hom):
        """reads in gt_pl_gq, and qual_score, returns rows with qual_score >= 20 and gq >= 20 (het), gq >= 40 (hom)"""
        
        gq_score = []
        genotype = []
        qual_score = []
        
        
        qual_gq_filtered_WES_rows = []
        
        for i in data:
                #skips truncated lines
                if i[0].startswith('GL'):
                        continue
                #the -1 index is always the last element of a python list
                else:
                        gq_score.append(i[-1].split(':')[-2])
                        qual_score.append(i[5])
                        genotype.append(i[-1].split(':')[0])
        
        #This for loop goes through each set of data, and ensures that the quality/gq scores meet a certain threshold
        for i in xrange(len(gq_score)):
                if genotype[i] in ['0/1', '1/0'] and float(qual_score[i]) >= input_qual:
                        if int(gq_score[i]) >= input_het:
                                qual_gq_filtered_WES_rows.append(data[i])
                elif genotype[i] == '1/1' and float(qual_score[i]) >= input_qual:
                        if int(gq_score[i]) >= input_hom:
                                qual_gq_filtered_WES_rows.append(data[i])

        
        return qual_gq_filtered_WES_rows
        
def filter_qual_RNA(data, input_qual, input_het, input_hom):
        """reads in gt_pl_gq, and qual_score, returns rows with qual_score >= 20 and gq >= 20 (het), gq >= 40 (hom) or values defined by user"""
        #the split indexes are slightly different due to the vcf format
        gq_score = [i[-1].split(':')[-1] for i in data]

        genotype = [i[-1].split(':')[0] for i in data]

        qual_score = [i[5] for i in data]


        qual_gq_filtered_RNA_rows = []

        for i in xrange(len(gq_score)):
                if genotype[i] in ['0/1', '1/0'] and float(qual_score[i]) >= input_qual:
                        if int(gq_score[i]) >= input_het:
                                qual_gq_filtered_RNA_rows.append(data[i])
                elif genotype[i] == '1/1' and float(qual_score[i]) >= input_qual:
                        if int(gq_score[i]) >= input_hom:
                                qual_gq_filtered_RNA_rows.append(data[i])

       

        return qual_gq_filtered_RNA_rows


def filter_snp_indel(qual_gq_filtered_rows):
        """filter rows into snps, and indels based on length of alt/ref"""
        
        length = []
        snps = []
        indels = []
        #loops through all of the rows with sufficient quality
        for i in xrange(len(qual_gq_filtered_rows)):
                temp = qual_gq_filtered_rows[i][4].split(',')

                for j in xrange(len(temp)):
                        length.append(len(temp[j]))
                #if all of the alt alleles have length 1, and the ref allele is length 1, append to snps
                if all(i == 1 for i in length) and len(qual_gq_filtered_rows[i][3]) == 1:
                        snps.append(qual_gq_filtered_rows[i])
                #otherwise, we consider it an indel
                else:
                        indels.append(qual_gq_filtered_rows[i])

                length = []
                temp = []

        return snps, indels


def write_processed_variants(file_name, snps, indels, headers, key_data):
        """defines naming schemes for snps/indels, then writes to file with original vcf format"""
        #creates the new naming scheme from the key file
        for i in key_data:      
                if i[3] == file_name:
                        snp_name = str(i[0]) + '_' + str(i[1]) + '-' + str(i[-1]) + '_WES' + '_snp.vcf'
                        indel_name = str(i[0]) + '_' + str(i[1]) + '-' + str(i[-1]) + '_WES' + '_indel.vcf'
                elif i[2] == file_name:
                        snp_name = str(i[0]) + '_' + str(i[1]) + '-' + i[-1] + '_RNA' + '_snp.vcf'
                        indel_name = str(i[0]) + '_' + str(i[1]) + '-' + i[-1] + '_RNA' + '_indel.vcf'
                else:
                        'File not present in key'
        #standard write functions
        with open(snp_name, 'w') as w:
                for line in headers:
                        w.write(line + '\n')
                
                for row in snps:
                        for index, column in enumerate(row):
                                if index != len(row) - 1:
                                        w.write('%s\t' % column)
                                else:
                                        w.write('%s\n' % column)

        with open(indel_name, 'w') as x:
                for line in headers:
                        x.write(line + '\n')
                
                for row in indels:
                        for index, column in enumerate(row):
                                if index != len(row) - 1:
                                        x.write('%s\t' % column)
                                else:
                                        x.write('%s\n' % column)

        
def main():
        #ensures proper number of arguments
        if len(sys.argv) != 2:
                print 'Please call script: {0} <keyfile>'.format(sys.argv[0])
                sys.exit(1)
        
        first_input = str(raw_input("""Do you want default filtering settings? ('y' or 'n') """))
        toggle = first_input.lower()
        #checks for valid inputs for quality filters
        if toggle.isalpha():
                if toggle == 'y':
                        input_qual = 20
                        input_het = 20
                        input_hom = 40
                
                elif toggle == 'n':
                        try:
                                input_qual = int(raw_input("Quality score? "))
                                input_het = int(raw_input("Heterozygous GQ? "))
                                input_hom = int(raw_input("Homozygous GQ? "))
                                if input_qual < 0 or input_het < 0 or input_hom < 0:
                                        print 'Please enter positive integers'
                                        sys.exit(1)
                                
                        except ValueError:
                                print 'Please enter only integers'
                                sys.exit(1)
                else:
                        print "Please enter only y or n"
                        sys.exit(1)
        else:
                print "Please enter only y or n"
                sys.exit(1)
        
                
        #key data read in
        key_file = sys.argv[1]
        key_headers, key_data = read_data(key_file)

        #list of RNA and WES files, change the indices if you change the position in the key file
        WES_files = [i[3] for i in key_data]
        RNA_files = [i[2] for i in key_data]
        all_vcf_files = WES_files + RNA_files

        for index, file_name in enumerate(all_vcf_files):   #parse in series, and write out final final
        
                if file_name in WES_files:
                        
                        headers, data = read_data(file_name)
                        print file_name, ': Data read into buffer'
                        qual_gq_filtered_WES_rows = filter_qual_WES(data, input_qual, input_het, input_hom)
                        print file_name, ': Variants filtered by quality'
                        snps, indels = filter_snp_indel(qual_gq_filtered_WES_rows)
                        print file_name, ': Variants split into snps/indels'
                        write_processed_variants(file_name, snps, indels, headers, key_data)
                        print file_name, ': Variants written to file'
                        print str(round((100*(index + 1)) / len(all_vcf_files), 3)) + '% complete\n'
                
                elif file_name in RNA_files:
               
                        headers, data = read_data(file_name)
                        print file_name, ': Data read into buffer'
                        qual_gq_filtered_RNA_rows = filter_qual_RNA(data, input_qual, input_het, input_hom)
                        print file_name, ': Variants filtered by quality'
                        snps, indels = filter_snp_indel(qual_gq_filtered_RNA_rows)
                        print file_name, ': Variants split into snps/indels'
                        write_processed_variants(file_name, snps, indels, headers, key_data)
                        print file_name, ': Variants written to file'
                        print str(round((100*(index + 1)) / len(all_vcf_files), 3)) + '% complete\n'


if __name__ == "__main__":
        main()
