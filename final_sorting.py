#!/usr/bin/env python


from __future__ import division
import os
import sys
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


	return data


def main():

	if len(sys.argv) != 2:
		print "Please call script: {0} <key file>".format(sys.argv[0])

	key_file = sys.argv[1]
	key_data = read_data(key_file)

	all_files = glob.glob('*')


	#outputs from processing script
	processed_files = glob.glob('*_snp.vcf')
	unprocessed_indels = glob.glob('*_indel.vcf')

	#outputs from gsearch and merge script
	gsearch_files = glob.glob('*_shared.vcf')
	merge_files = glob.glob('*_merged.vcf')
	gz_files = glob.glob('*vcf.gz')
	tabix_files = glob.glob('*vcf.gz.tbi')
	gsearch_merge_files = gsearch_files + merge_files + gz_files + tabix_files
	

	#output from VEP calling script
	annotated_files = glob.glob('*_annotated.vcf*')

	#all outputs from binning script
	monoallelic_files = glob.glob('*_RNA-hom_WES-het.vcf')
	other_mismatch = glob.glob('*_RNA-het_WES-hom.vcf')
	matching_het = glob.glob('*_het-matching.vcf')
	matching_hom = glob.glob('*_hom-matching.vcf')
	matrix_counts = glob.glob('*_matrix_counts.txt')
	match_coordinates = glob.glob('*_match_coordinates.txt')
	binning_files = monoallelic_files + other_mismatch + matching_het + matching_hom + matrix_counts + match_coordinates

	#all outputs from variant compare script
	monoallelic_common = glob.glob('*_monoallelic_common*.vcf')
	monoallelic_unique = glob.glob('*_monoallelic_unique.vcf')
	gene_lists = glob.glob('*_genelist.txt')
	gene_dictionaries = glob.glob('*_gene_dictionary.csv')
	lineage_files = glob.glob('*_traced_WES.txt')
	variant_comparison_files = monoallelic_common + monoallelic_unique + gene_lists + gene_dictionaries + lineage_files

	#this creates a unique set of all of the family IDs
	family_ids = []
	for file_name in key_data:
		if file_name[0] not in family_ids and file_name[0].isdigit():
			family_ids.append(file_name[0])
		else:
			continue

	#this grabs the original files, and the scripts
	scripts = [files for files in all_files if files.endswith('.py')]
	RNA_original_files = [i[2].strip() for i in key_data]
	WES_original_files = [i[3].strip() for i in key_data]
	original_files = RNA_original_files + WES_original_files + scripts


	if len(all_files) != 1 + len(unprocessed_indels) + len(processed_files) + len(gsearch_merge_files) + len(annotated_files) + len(binning_files) + len(variant_comparison_files) + len(original_files):
		print 'Script does not account for all file types'
		sys.exit(1)
	else:
		print 'Initalizing directories and moving files'

	os.system('mkdir original_files_and_scripts')

	directories = ['processed_files', 'gsearch_merge_files', 'binning_files', 'annotated_files', 'variant_comparison_files']

	#initializes all needed directories
	for family_id in family_ids:
		os.system('mkdir %s' % family_id)
		os.system('mkdir %s/snp' % family_id)
		for directory in directories:
			os.system('mkdir %s/snp/%s' % (family_id, directory))
		os.system('mkdir %s/indel' % family_id)

	#moves original data files to original folder
	for vcf in all_files:
		if vcf in original_files or (vcf == 'sampleKey_truncated.txt'):
			os.system('mv %s %s/' % (vcf, 'original_files_and_scripts'))

		else:
			family_id = vcf.split('_')[0]

			if vcf in processed_files:
				os.system('mv %s %s/snp/%s' % (vcf, family_id, directories[0]))

			elif vcf in gsearch_merge_files:
				os.system('mv %s %s/snp/%s' % (vcf, family_id, directories[1]))

			elif vcf in binning_files:
				os.system('mv %s %s/snp/%s' % (vcf, family_id, directories[2]))

			elif vcf in annotated_files:
				os.system('mv %s %s/snp/%s' % (vcf, family_id, directories[3]))

			elif vcf in variant_comparison_files:
				os.system('mv %s %s/snp/%s' % (vcf, family_id, directories[4]))

			elif 'indel' in vcf:
				os.system('mv %s %s/indel' % (vcf, family_id))
		
			else:
				print vcf, 'File unaccounted for by script'
				sys.exit(1)

			

if __name__ == "__main__":
	main()