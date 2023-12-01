import argparse
import os
import shutil
import stat
import time
import logging
from PyPDF2 import PdfFileReader, PdfFileWriter

def setup_logger():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()])

def main():
    parser = argparse.ArgumentParser(
        description="Tool to remove password set on PDF files and organize them - (Stefano Crapanzano - s.crapanzano@gmail.com)")
    parser.add_argument('source_directory', help='Directory containing the PDFs with password protection')
    parser.add_argument('destination_directory', help='Directory where the new PDFs will be placed')
    parser.add_argument('-a', '--age_of_file_to_treat', type=float,
                        help='Age in seconds of file to be treated (optional)')
    parser.add_argument('-p', '--max_pages', type=int,
                        help='Threshold for the maximum number of pages in a PDF file (optional)')
    args = parser.parse_args()

    source_directory = args.source_directory
    destination_directory = args.destination_directory
    age_of_file_to_treat = args.age_of_file_to_treat
    max_pages = args.max_pages

    setup_logger()
    logger = logging.getLogger(__name__)

    timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())
    date_exec = timestamp

    destination_backup_folder_name = os.path.join(destination_directory, f'{date_exec}_backup')
    destination_new_folder_name = os.path.join(destination_directory, f'{date_exec}_new')

    nb_pdf_corrected = 0
    nb_files_moved = 0

    try:
        os.makedirs(destination_backup_folder_name, exist_ok=True)
        os.makedirs(destination_new_folder_name, exist_ok=True)

        for file_name in os.listdir(source_directory):
            source_file_path = os.path.join(source_directory, file_name)

            if not os.path.isfile(source_file_path):
                continue

            if age_of_file_to_treat and file_age_in_seconds(source_file_path) < age_of_file_to_treat:
                continue

            old_file_name = file_name
            file_name = file_name.lower().replace('.pdf.convert', '.pdf').replace('.pdf.import', '.pdf')
            destination_file_path = os.path.join(destination_new_folder_name, file_name)

            if file_name.endswith(('.pdf', '.pdf.convert', '.pdf.import')):
                try:
                    with open(source_file_path, 'rb') as f:
                        file_reader = PdfFileReader(f)
                        num_pages = len(file_reader.pages)

                        if max_pages is not None and num_pages > max_pages:
                            logger.warning(f"Skipping {source_file_path}. Exceeds maximum allowed pages ({max_pages}).")
                            continue

                        logger.info(f"{source_file_path} > Nb pages: {num_pages}; Is Encrypted: {file_reader.isEncrypted}")

                        pdf_writer = PdfFileWriter()
                        pdf_writer.addPages(file_reader.pages)

                        with open(destination_file_path, 'wb') as pdf_output_file:
                            pdf_writer.write(pdf_output_file)

                    nb_pdf_corrected += 1
                except Exception as e:
                    logger.error(f"Exception occurred with creation of file {destination_file_path}: {e}")

            try:
                shutil.move(source_file_path, os.path.join(destination_backup_folder_name, old_file_name))
                nb_files_moved += 1
            except Exception as e:
                logger.error(f"Exception occurred while moving from [{source_file_path}] to [{destination_backup_folder_name + old_file_name}]: {e}")

        logger.info(f"{nb_files_moved} file(s) have been moved to {destination_backup_folder_name}")
        logger.info(f"{nb_pdf_corrected} pdf file(s) have been treated.")
        input("Press enter to continue...")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

def file_age_in_seconds(pathname):
    return time.time() - os.stat(pathname)[stat.ST_MTIME]

if __name__ == "__main__":
    main()
