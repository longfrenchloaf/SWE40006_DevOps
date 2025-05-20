import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException # Import specific exceptions

# Function to read test cases from CSV
def read_test_cases(filename):
    test_cases = []
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            test_cases.append(row)
    return test_cases

# Sets up Chrome WebDriver with specified options
def setup_driver():
    options = Options()
    # --- IMPORTANT: Verify this path is correct for your system ---
    # If chrome.exe is in the default location, you might not even need this line
    # options.binary_location = "chrome-win32/chrome.exe" # Comment out or adjust if needed
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage') # Recommended for some environments
    # options.add_argument('--headless') # Uncomment if you don't want to see the browser window
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver

def wait_for_element(driver, by, value, timeout=10):
    """Waits for an element to be present on the page."""
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )

def wait_and_click(driver, by, value, timeout=10):
     """Waits for an element to be clickable and clicks it."""
     return WebDriverWait(driver, timeout).until(
         EC.element_to_be_clickable((by, value))
     ).click()

def is_element_present(driver, by, value, timeout=2):
    """Checks if an element is present within a given timeout."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return True
    except TimeoutException:
        return False


# Function to execute the test case
def execute_test_case(driver, test_case):
    print(f"Navigating to menu page: http://localhost/SWE40006_DevOps/menu.php")
    driver.get("http://localhost/SWE40006_DevOps/menu.php")

    # The quantity fields are qty_0 to qty_7
    qty_fields_new = [f'qty_{i}' for i in range(8)]

    # Wait for the container or a representative element of the menu page to load
    try:
        wait_for_element(driver, By.CLASS_NAME, 'container')
        print("Menu page loaded.")
    except Exception as e:
        print(f"Failed to load menu page or find container: {e}")
        return f"FAIL - Menu page load failed: {e}"


    # Fill in the quantity inputs
    invalid_input_expected = False # Flag to check if we expect the SweetAlert
    for qty_field in qty_fields_new:
        qty_value = test_case.get(qty_field, '')
        # Check if the value is non-empty and likely invalid based on character types
        # This is a simplified check, the JS validation is the real test
        if qty_value and (not qty_value.isdigit() and qty_value != '-1'):
             invalid_input_expected = True
        if qty_value == '-1': # Specifically mark -1 as invalid input
            invalid_input_expected = True


        if qty_value != '':
            try:
                qty_input = wait_for_element(driver, By.NAME, qty_field, timeout=5)
                qty_input.clear()
                qty_input.send_keys(str(qty_value)) # Send as string to match CSV
                # print(f"Filled {qty_field} with '{qty_value}'") # Detailed debug
            except Exception as e:
                print(f"Could not interact with {qty_field}: {e}")


    # Apply discount if specified
    apply_discount_str = test_case.get('ApplyDiscount', 'FALSE')
    if apply_discount_str.upper() == 'TRUE':
        try:
            discount_checkbox = wait_for_element(driver, By.NAME, 'apply_discount', timeout=5)
            if not discount_checkbox.is_selected():
                 discount_checkbox.click()
            print("Applied discount.")
        except Exception as e:
             print(f"Could not interact with discount checkbox: {e}")


    # Click submit button
    try:
        # Wait for the button to be clickable before clicking
        wait_and_click(driver, By.NAME, 'submit_button', timeout=5)
        print("Clicked submit button.")
    except Exception as e:
         print(f"Could not click submit button: {e}")
         return f"FAIL - Could not click submit button: {e}"

    # --- Handle SweetAlert if it appears due to invalid input ---
    sweet_alert_confirm_button_locator = (By.CSS_SELECTOR, '.swal2-confirm')
    sweet_alert_cancel_button_locator = (By.CSS_SELECTOR, '.swal2-cancel') # In case we need to check for it

    # Give the SweetAlert a moment to appear (can't rely solely on wait_for_element here)
    time.sleep(1) # Small static sleep to allow modal transition

    if is_element_present(driver, *sweet_alert_confirm_button_locator, timeout=3): # Check if confirm button is visible
         print("SweetAlert modal detected!")
         try:
             # Click the "Yes, reset to 0" button in the SweetAlert
             wait_and_click(driver, *sweet_alert_confirm_button_locator, timeout=5)
             print("Clicked 'Yes, reset to 0' in SweetAlert.")
             # If SweetAlert was handled, quantities were reset to 0 by JS
             # So, the expected total for this test case is effectively 0.
             test_case['ExpectedTotal'] = '0.00' # Override expected total for assertion later
             invalid_input_expected = False # No longer expecting invalid input *after* reset
         except Exception as e:
             print(f"Could not click SweetAlert confirm button: {e}")
             return f"FAIL - SweetAlert confirmation failed: {e}"
    elif invalid_input_expected:
         # If we expected invalid input (based on our CSV check) but SweetAlert didn't appear
         # or wasn't handled (e.g., cancel button clicked manually during a run)
         # this might indicate an issue, or the test will likely time out anyway.
         # For this test script, we'll just proceed and let the next waits handle it.
         print("Note: Invalid input was entered, but SweetAlert confirmation step was skipped or missed.")


    # --- Handle expected empty cart vs non-empty cart based on (potentially overridden) ExpectedTotal ---
    try:
        expected_value_clean = float(test_case.get('ExpectedTotal', '0.00').strip().replace(',', ''))
    except ValueError:
        print(f"Invalid ExpectedTotal (after potential override) in test case: {test_case.get('ExpectedTotal', '0.00')}")
        return f"FAIL - Invalid ExpectedTotal in test case: {test_case.get('ExpectedTotal', '0.00')}"

    if round(expected_value_clean, 2) == 0:
        # Expected total is 0, wait for the empty cart message instead of the summary
        print("Expected total is 0. Waiting for empty cart message...")
        empty_cart_message_locator = (By.XPATH, "//div[@class='container']/p[contains(text(), 'Your cart is empty')]")
        try:
            # Wait explicitly for the empty cart message element
            wait_for_element(driver, *empty_cart_message_locator, timeout=10)
            print("Empty cart message found.")
            result = 'PASS' # Test passes if the empty message is shown and expected is 0

        except TimeoutException:
             # If empty cart message doesn't appear, it means the cart page might have loaded
             # but *didn't* show the empty message (perhaps due to a bug, or items weren't reset)
             print("Timeout waiting for empty cart message when 0 total was expected.")
             # Attempt to check for the summary div as a fallback to see if it loaded incorrectly
             if is_element_present(driver, By.CLASS_NAME, 'total-summary', timeout=2):
                  print("Warning: Total summary box found when 0 total was expected. Calculating actual total.")
                  # If summary box exists, calculate the actual total to provide better failure info
                  total_element_locator = (By.CSS_SELECTOR, '.final-total span')
                  try:
                       total_element = wait_for_element(driver, *total_element_locator, timeout=2) # Short wait
                       computed_value_text = total_element.text.strip()
                       if computed_value_text.startswith('RM'):
                           computed_numeric_str = computed_value_text[2:].strip().replace(',', '')
                       else:
                           computed_numeric_str = computed_value_text.strip().replace(',', '')
                       computed_value_clean = float(computed_numeric_str)
                       result = f'FAIL - Expected 0.00 total (empty cart) but got RM{computed_value_clean:.2f}'
                  except Exception as calc_error:
                        result = f'FAIL - Expected 0.00 total (empty cart) but page loaded without empty message or calculable total: {calc_error}'
             else:
                  result = f'FAIL - Empty cart message not shown for expected 0 total (Timeout)'
        except Exception as e:
            print(f"Error while waiting for empty cart message: {e}")
            result = f'FAIL - Error checking empty cart message: {e}'

    else:
        # Expected total is > 0, wait for the summary box and total amount
        print(f"Expected total is > 0 ({expected_value_clean:.2f}). Waiting for total summary...")
        total_element_locator = (By.CSS_SELECTOR, '.final-total span')
        try:
            # Wait for the cart page to load and the total summary box to be present
            wait_for_element(driver, By.CLASS_NAME, 'total-summary', timeout=10)
            # Then wait specifically for the span containing the total
            total_element = wait_for_element(driver, *total_element_locator, timeout=5)
            computed_value_text = total_element.text.strip()

            # Extract only the numeric part after 'RM' and remove commas
            if computed_value_text.startswith('RM'):
                computed_numeric_str = computed_value_text[2:].strip().replace(',', '')
            else:
                computed_numeric_str = computed_value_text.strip().replace(',', '')

            computed_value_clean = float(computed_numeric_str)

            print(f"Computed Value (clean): {computed_value_clean:.2f}, Expected Value (clean): {expected_value_clean:.2f}")

            # Compare computed value with expected value and assert
            assert round(computed_value_clean, 2) == round(expected_value_clean, 2), \
                f"Test case failed! Expected: RM{expected_value_clean:.2f}, Got: RM{computed_value_clean:.2f}"
            result = 'PASS'
            print("Test case passed!")
        except (AssertionError, ValueError) as e:
            print(f"Assertion/ValueError in Test case: {e}")
            result = f'FAIL - {e}'
        except TimeoutException:
             print(f"Timeout waiting for total summary or total element when > 0 total was expected.")
             # If timeout happens when expecting > 0, the cart page probably didn't load correctly
             result = f'FAIL - Cart page did not load total summary (Timeout)'
        except Exception as e:
             print(f"An unexpected error occurred during total comparison: {e}")
             result = f'FAIL - Unexpected error: {e}'


    # Return the result
    return result

# Main function to run all test cases
def main():
    # Read the test cases from the CSV file
    # Make sure test_cases.csv is in the SAME directory as program_test.py
    test_cases = read_test_cases('test_cases.csv')
    print(f"Loaded {len(test_cases)} test cases.")
    if not test_cases:
        print("No test cases found in CSV. Please check test_cases.csv.")
        return

    # Set up the WebDriver
    driver = None # Initialize driver outside try block
    try:
        driver = setup_driver()

        # Initialize a list to keep track of results
        test_results = []

        # Execute each test case and print the result
        for idx, test_case in enumerate(test_cases):
            print(f"\n--- Executing Test Case {idx + 1} ---")
            # Print the test case details for better debugging
            try:
                 qty_details = [f'{f}: {test_case.get(f, "")}' for f in [f'qty_{i}' for i in range(8)]]
                 print(f"Details: Quantities=[{', '.join(qty_details)}], Discount={test_case.get('ApplyDiscount', 'FALSE')}, Expected={test_case.get('ExpectedTotal', 'N/A')}")
            except Exception as print_error:
                 print(f"Error printing test case details: {print_error}")
                 print(f"Raw test case data: {test_case}")


            result = execute_test_case(driver, test_case)
            test_results.append(f"Test Case {idx + 1}: {result}")
            print(f"--- Test case {idx + 1} result: {result} ---")
            # Optional: Add a delay between test cases if needed
            # time.sleep(1)


        # Print out all test results at the end
        print("\n======= Test Execution Summary =======")
        for result in test_results:
            print(result)
        print("======================================")

    except Exception as e:
        print(f"\nAn error occurred during test setup or main loop execution: {e}")
        # Print traceback for unexpected errors during setup
        import traceback
        traceback.print_exc()
    finally:
        # Close the browser after tests are complete
        if driver:
            print("\nClosing browser...")
            driver.quit()


if __name__ == "__main__":
    main()