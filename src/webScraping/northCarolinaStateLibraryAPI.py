from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
from selenium.common.exceptions import WebDriverException
from webScraping.baseScraping import BaseScraping
import util.dictionaryValidationMethod as vd
from selenium.webdriver.chrome.service import Service as ChromeService
from webScraping.webDriverManager import WebDriverManager
import logging 

class NorthCarolinaStateLibraryAPI(BaseScraping):

    def __init__(self):
        try:
            self.driver = WebDriverManager.get_driver()
        except RuntimeError as e:
            logging.error("Failed to initialize NorthCarolinaStateLibraryAPI due to WebDriver issue.")
            logging.info(e)
            raise
        self.catalog_data = {"ISBN": [], "OCN": "", "LCCN": [], "LCCN_Source": []}

        
    def send_dictionary(self):
        self.catalog_data = vd.optimize_dictionary(self.catalog_data)
        return {k.lower(): v for k, v in self.catalog_data.items()}

    def fetch_metadata(self, identifier, input_type):

        try:

            self.catalog_data = {"ISBN": [], "OCN": "", "LCCN": [], "LCCN_Source": []}
            if not self.is_online():
                print("No internet connection available at the start.")
                return self.send_dictionary() 
            identifier = identifier.strip("\n")
            input_type = input_type.upper()

            if (input_type != "OCN") and (input_type != "ISBN"):
                # print("Please select either 'ISBN' or 'OCN' as your second argument.")
                return {k.lower(): v for k, v in self.catalog_data.items()}

            elif input_type == "ISBN":

                self.catalog_data["ISBN"].append(identifier)

                self.driver.get(f"https://catalog.lib.ncsu.edu/?search_field=isbn_issn&q={identifier}")

                time.sleep(5)

                try:
                    # Get the name of the book and click on it.
                    title = self.driver.find_element(By.CLASS_NAME, "index_title")
                    title_text = title.text[title.text.index(" ") + 1:]
                    link_to_title = self.driver.find_element(By.LINK_TEXT, title_text)
                    link_to_title.click()

                    time.sleep(5)

                    marc_view = self.driver.find_element(By.XPATH, "//*[@data-target='#marc-modal']")
                    marc_view.click()

                    time.sleep(5)

                    body = self.driver.find_element(By.TAG_NAME, "body")
                    body_text = body.text.replace("\n", " ")

                    try:
                        index_of_ocn = body_text.index("(OCoLC)")
                        if body_text.index(" ", index_of_ocn) > body_text.index("|", index_of_ocn):
                            self.catalog_data["OCN"] = body_text[index_of_ocn + 7: body_text.index("|", index_of_ocn)]
                        else:
                            self.catalog_data["OCN"] = body_text[index_of_ocn + 7: body_text.index(" ", index_of_ocn)]
                    except ValueError:
                        pass

                    def find_occurrences_using_index(input_string, search_string):
                        indices = []
                        start_index = 0

                        while True:
                            try:
                                index = input_string.index(search_string, start_index)
                                indices.append(index)
                                start_index = index + 1
                            except ValueError:
                                break

                        return indices

                    indexes_of_fifty_part_one = find_occurrences_using_index(body_text, "050 0 0 ")
                    indexes_of_fifty_part_two = find_occurrences_using_index(body_text, "050 4 ")
                    indexes_of_fifty = indexes_of_fifty_part_one + indexes_of_fifty_part_two

                    for index_of_fifty in indexes_of_fifty:
                        index_of_first_portion = body_text.index("|a", index_of_fifty)
                        first_portion = body_text[
                                        index_of_first_portion + 2: body_text.index("|b", index_of_first_portion)]
                        index_of_second_portion = body_text.index("|b", index_of_fifty)
                        index_of_intermediate_space = body_text.index(" ", index_of_second_portion)
                        index_of_final_space = body_text.index(" ", index_of_intermediate_space + 1)
                        second_portion = body_text[index_of_second_portion + 2: index_of_final_space]

                        index_of_filter_space = body_text.index(" ", index_of_first_portion)
                        if index_of_filter_space < index_of_second_portion:
                            lccn = body_text[index_of_first_portion + 2: index_of_filter_space]
                        else:
                            lccn = first_portion + second_portion
                        self.catalog_data["LCCN"].append(lccn)
                        self.catalog_data["LCCN_Source"].append("NCSU")

                    return self.send_dictionary()

                except NoSuchElementException:
                    return self.send_dictionary()

                except ValueError:
                    return self.send_dictionary()

            elif input_type == "OCN":

                self.catalog_data["OCN"] = identifier

                self.driver.get(f"https://catalog.lib.ncsu.edu/?search_field=all_fields&q={identifier}")

                time.sleep(5)

                try:

                    title = self.driver.find_element(By.CLASS_NAME, "index_title")
                    title_text = title.text[title.text.index(" ") + 1:]
                    link_to_title = self.driver.find_element(By.LINK_TEXT, title_text)
                    link_to_title.click()

                    time.sleep(5)

                    body = self.driver.find_element(By.TAG_NAME, "body")
                    body_text = body.text.replace("\n", " ")

                    try:
                        index_of_isbn = body_text.index("ISBN: ")
                        index_of_end_of_relevant_text = body_text.index(": ", index_of_isbn + 6)
                        list_isbns = body_text[index_of_isbn + 6: index_of_end_of_relevant_text].split(" ")

                        def contains_digits(input_string):
                            return any(char.isdigit() for char in input_string)

                        for item in list_isbns:
                            if contains_digits(item):
                                self.catalog_data["ISBN"].append(item)

                    except ValueError:
                        pass

                    marc_view = self.driver.find_element(By.XPATH, "//*[@data-target='#marc-modal']")
                    marc_view.click()

                    time.sleep(5)

                    body = self.driver.find_element(By.TAG_NAME, "body")
                    body_text = body.text.replace("\n", " ")

                    def find_occurrences_using_index(input_string, search_string):
                        indices = []
                        start_index = 0

                        while True:
                            try:
                                index = input_string.index(search_string, start_index)
                                indices.append(index)
                                start_index = index + 1
                            except ValueError:
                                break

                        return indices

                    indexes_of_fifty_part_one = find_occurrences_using_index(body_text, "050 0 0 ")
                    indexes_of_fifty_part_two = find_occurrences_using_index(body_text, "050 4 ")
                    indexes_of_fifty = indexes_of_fifty_part_one + indexes_of_fifty_part_two

                    for index_of_fifty in indexes_of_fifty:
                        index_of_first_portion = body_text.index("|a", index_of_fifty)
                        first_portion = body_text[
                                        index_of_first_portion + 2: body_text.index("|b", index_of_first_portion)]
                        index_of_second_portion = body_text.index("|b", index_of_fifty)
                        index_of_intermediate_space = body_text.index(" ", index_of_second_portion)
                        index_of_final_space = body_text.index(" ", index_of_intermediate_space + 1)
                        second_portion = body_text[index_of_second_portion + 2: index_of_final_space]

                        index_of_filter_space = body_text.index(" ", index_of_first_portion)
                        if index_of_filter_space < index_of_second_portion:
                            lccn = body_text[index_of_first_portion + 2: index_of_filter_space]
                        else:
                            lccn = first_portion + second_portion
                        self.catalog_data["LCCN"].append(lccn)
                        self.catalog_data["LCCN_Source"].append("NCSU")

                    return self.send_dictionary()

                except NoSuchElementException:
                    return self.send_dictionary()

                except ValueError:
                    return self.send_dictionary()

        except WebDriverException as e:
            logging.error(f"Encountered a WebDriverException: {e}")

            #Retry logic with reinitialization
            for attempt in range(3):  # Retry up to 3 times
                try:
                    logging.info(f"Retrying Driver restart, attempt {attempt+1}")
                    self.driver.restart_driver()  
                    return self.send_dictionary() 
                except WebDriverException as retry_exception:
                    logging.error(f"Retry attempt {attempt+1} failed: {retry_exception}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
            logging.error("All retry attempts failed. Moving on to the next task.")
            return self.send_dictionary() 
        
        except Exception as e:
            logging.error(f"Encountered an unexpected exception: {e}") 
            self.send_dictionary()  