# tests/test_food_billing_ui.py

import pytest
import time
import pandas as pd # Using pandas for easier CSV reading
import os # Import os to read environment variables

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

# --- Helper function to read CSV data ---
def read_csv_data(filename='test_cases.csv'):
    """Reads test case data from a CSV file."""
    test_cases = []
    try:
        script_dir = os.path.dirname(__file__)
        csv_filepath = os.path.join(script_dir, filename)

        print(f"Attempting to read CSV from: {csv_filepath}")

        # Using pandas for easier CSV reading.
        # Using 'dtype=str' can force pandas to read everything as strings initially,
        # preserving the exact input from the CSV for numeric columns.
        df = pd.read_csv(csv_filepath, dtype=str) # <-- Read all data columns as strings

        data = []
        for index, row in df.iterrows():
             test_case = row.to_dict()

             # Clean up quantity values. They are already strings due to dtype=str.
             for i in range(8):
                 key = f'qty_{i}'
                 # Get the value as string, strip whitespace, handle potential None/NaN after to_dict
                 qty_value_str = test_case.get(key, '').strip() if pd.notna(test_case.get(key)) else ''

                 # Store the cleaned string back. We'll parse numbers in helpers.
                 test_case[key] = qty_value_str

             # Standardize discount to uppercase string
             test_case['ApplyDiscount'] = test_case.get('ApplyDiscount', '').upper().strip() # It's already a string

             # Add a unique identifier
             test_case['test_id'] = f"case_{index + 1}"

             data.append(test_case)

        if not data:
             print(f"Warning: No test cases found in {filename} after reading.")

        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"Test case CSV not found at {filename}. Please check the path: {csv_filepath}")
    except Exception as e:
        raise RuntimeError(f"Error reading or processing CSV file {filename} at {csv_filepath}: {e}")

# --- Refined Helper Functions for Scenario Classification ---

def is_valid_positive_number(qty_str):
    """Checks if a string can be converted to a non-negative float."""
    if qty_str is None or qty_str.strip() == '':
        return False # Empty string is not a valid number input in this context
    try:
        num = float(qty_str)
        return num >= 0
    except ValueError:
        return False # Cannot be converted to a number

def is_valid_positive_integer_string(qty_str):
    """Checks if a string is composed only of digits (>= 0 integer)."""
    if qty_str is None or qty_str.strip() == '':
        return False
    return qty_str.strip().isdigit() # isdigit() checks for non-negative integers

def has_invalid_quantity_input(test_case):
    """Checks if any quantity input is invalid (e.g., text, negative, non-integer float)."""
    qty_ids = [f'qty_{i}' for i in range(8)]
    for qty_id in qty_ids:
        qty_value = test_case.get(qty_id, '').strip()
        if qty_value == '':
            continue # Empty string is treated as 0 quantity, not invalid input

        # Check for obvious invalid types (non-numeric strings, including negative signs not as part of number)
        if not is_valid_positive_number(qty_value):
             # This covers cases like 'meow', '*', '-1'
             print(f"Detected invalid input (not valid positive number): {qty_id}='{qty_value}'") # Debugging
             return True

        # After confirming it's a valid non-negative number, check if it's a non-integer float
        try:
             num = float(qty_value)
             # Check if it has a fractional part AND that fractional part is non-zero
             # Or simply check if it's different from its integer representation
             if num != int(num):
                  print(f"Detected non-integer float input: {qty_id}='{qty_value}'") # Debugging
                  # Assuming the application considers non-integer floats invalid
                  return True
        except ValueError:
             # Should not happen if is_valid_positive_number passed, but as a safeguard
             print(f"Error converting potential number {qty_value} to float/int.")
             return True # Treat as invalid if conversion fails unexpectedly

    return False # No invalid input found based on these criteria

def all_quantities_zero_or_empty(test_case):
    """Checks if all quantities are effectively zero (empty string or '0')."""
    qty_ids = [f'qty_{i}' for i in range(8)]
    for qty_id in qty_ids:
        qty_value = test_case.get(qty_id, '').strip()
        # If any quantity is *not* empty AND represents a positive number > 0, it's not an empty cart
        if is_valid_positive_number(qty_value) and float(qty_value) > 0:
             return False
    return True # All quantities are empty string or evaluate to 0

def has_valid_order_scenario(test_case):
    """Checks if the input data represents a valid order scenario."""
    # A valid order scenario is one that is NOT invalid AND NOT an empty cart.
    # It also implicitly requires at least one positive quantity to be classified as NOT empty.
    is_invalid = has_invalid_quantity_input(test_case)
    is_empty = all_quantities_zero_or_empty(test_case)

    # If it's not invalid AND not empty, it must be a valid order scenario.
    # We double-check that at least one quantity is positive, though all_quantities_zero_or_empty should cover the opposite.
    has_any_positive_qty = any(is_valid_positive_number(test_case.get(f'qty_{i}', '')) and float(test_case.get(f'qty_{i}', '')) > 0 for i in range(8))

    return not is_invalid and not is_empty and has_any_positive_qty


# --- Fixture for Test Data Loading and Parameterization ---
# This fixture will load data once per module scope, and then provide each item
# from the returned list as the 'test_case' argument to the test function.
# The ids=lambda... part provides better names in pytest output using the 'test_id' key.
@pytest.fixture(scope="module", params=read_csv_data('test_cases.csv'), ids=lambda test_case: test_case.get('test_id', 'unknown_id'))
def test_case(request):
    """Pytest fixture to load and parameterize test data from CSV."""
    # 'request.param' contains the current test case dictionary.
    return request.param

# --- Fixture for WebDriver Setup ---
# This fixture sets up the browser before tests run and quits it afterwards.
# scope="module" means one browser instance for all tests in this file.
# scope="function" means a fresh browser for each test.
@pytest.fixture(scope="module")
def driver():
    """Pytest fixture to set up and tear down the Selenium WebDriver."""
    options = Options()
    # options.binary_location = "chrome-win32/chrome.exe" # Uncomment or adjust if needed
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--headless') # UNCOMMENT this for CI/headless execution (no visible browser window)
    # options.add_argument('--disable-gpu') # Might be needed for headless on some systems
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    # Add option to bypass certificate errors if testing against http locally or with self-signed certs
    # options.add_argument('--ignore-certificate-errors')

    # Specify the path to your chromedriver if it's not in PATH
    # from selenium.webdriver.chrome.service import Service
    # service = Service(executable_path='/path/to/your/chromedriver')
    # driver = webdriver.Chrome(service=service, options=options)

    print("\nSetting up browser...") # Print during setup
    driver = webdriver.Chrome(options=options) # Assumes chromedriver is in PATH or specified via service
    yield driver
    print("\nClosing browser...") # Print during teardown
    driver.quit()


# --- Helper functions (wait_for_element, etc. - adapted from your script) ---
# These functions need the 'driver' instance passed to them.
# They use pytest.fail() to explicitly mark the test as failed on critical errors.

def wait_for_element(driver, by, value, timeout=10):
   """Waits for an element to be present on the page and returns it."""
   try:
       # print(f"Waiting for element: {by}={value}") # Debugging print
       return WebDriverWait(driver, timeout).until(
           EC.presence_of_element_located((by, value))
       )
   except TimeoutException:
       pytest.fail(f"Timeout waiting for element: {by}={value}")
   except Exception as e:
        pytest.fail(f"Error waiting for element {by}={value}: {e}")


def wait_and_click(driver, by, value, timeout=10):
    """Waits for an element to be clickable and clicks it."""
    try:
        # print(f"Waiting for element to be clickable: {by}={value}") # Debugging print
        WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        ).click()
        # print(f"Clicked element: {by}={value}") # Debugging print
    except TimeoutException:
       pytest.fail(f"Timeout waiting for element to be clickable: {by}={value}")
    except StaleElementReferenceException:
       print(f"Stale element reference when clicking: {by}={value}. Trying again.")
       time.sleep(1) # Add a small delay before retrying
       try:
           WebDriverWait(driver, timeout).until(
               EC.element_to_be_clickable((by, value))
           ).click()
       except Exception as e:
            pytest.fail(f"Failed clicking element {by}={value} after stale reference retry: {e}")
    except Exception as e:
         pytest.fail(f"Error clicking element {by}={value}: {e}")


def is_element_present(driver, by, value, timeout=2):
    """Checks if an element is present within a given timeout."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return True
    except TimeoutException:
        return False
    except Exception as e:
        # Avoid pytest.fail here as this is a check, not necessarily a critical error yet
        # print(f"Warning: Error checking for element presence ({by}={value}): {e}") # Debugging print
        return False

def wait_for_sweetalert(driver, title, timeout=10):
    """Waits for a SweetAlert modal with a specific title."""
    try:
        # Wait for the modal popup to be visible
        popup = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'swal2-popup'))
        )
        # Wait for the title element within the popup
        title_element = WebDriverWait(popup, timeout=2).until( # Search within the popup, faster timeout for title
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.swal2-title'))
        )
        detected_title = title_element.text.strip()
        print(f"Detected SweetAlert with title: '{detected_title}' (Expected: '{title}')")
        return title in detected_title # Use 'in' for partial match robustness

    except TimeoutException:
        # print(f"Timeout waiting for SweetAlert with title '{title}'.") # Avoid excessive printing on expected absence
        return False # No SweetAlert or specific title appeared within timeout
    except Exception as e:
         pytest.fail(f"Error waiting for SweetAlert with title '{title}': {e}")


def click_sweetalert_button(driver, text, timeout=5):
    """Clicks a SweetAlert button containing specific text."""
    # Look for buttons by class and text content
    # Use a more specific locator if possible, like swal2-confirm, swal2-cancel, swal2-deny
    button_locator = (By.XPATH, f"//button[contains(@class, 'swal2') and contains(text(), '{text}')]")
    try:
        wait_and_click(driver, *button_locator, timeout=timeout)
        print(f"Clicked SweetAlert button with text: '{text}'.")
    except Exception as e:
         pytest.fail(f"Failed to click SweetAlert button with text '{text}': {e}")


# --- Main Pytest Test Function ---
# This test function will be run multiple times by pytest, once for each test case
# provided by the parameterized 'test_case' fixture.
# Request 'driver' and 'test_case' fixtures as arguments.
def test_food_billing_scenario(driver, test_case):
    """Tests a food billing scenario based on CSV data."""
    # 'test_case' is the dictionary provided by the parameterized fixture.
    # Access CSV data using test_case.get('column_name', default_value).
    # Use pytest.fail() or assertions to indicate test failure.

    # Get the application URL from an environment variable set outside the test code
    # Provide a fallback for local testing if the variable isn't set
    # Use http://localhost:5000/ as the default for local development
    app_url = os.environ.get("APP_URL", "http://4.206.70.73:5000/")
    # Ensure URL ends with a slash for consistent joining
    if not app_url.endswith('/'):
        app_url += '/'

    # Print test case details for debugging using the dictionary
    qty_ids = [f'qty_{i}' for i in range(8)]
    # Ensure the print statement is correctly indented inside the test function
    qty_details = [f'{f}: "{test_case.get(f, "")}"' for f in qty_ids]
    print(f"\n--- Executing Test Case: {test_case.get('test_id', 'N/A')} ---") # Use the added test_id
    print(f"Details: Quantities=[{', '.join(qty_details)}], Discount={test_case.get('ApplyDiscount', 'FALSE')}, ExpectedTotal={test_case.get('ExpectedTotal', 'N/A')}")
    print(f"Target URL: {app_url}")


    # --- Step 1: Navigate to Menu Page ---
    # Ensure this block is correctly indented under the test function
    try:
        driver.get(app_url)
        print(f"Navigated to menu page: {app_url}")
    except Exception as e:
         pytest.fail(f"FAIL - Navigation failed to {app_url}: {e}")

    # Ensure this block is correctly indented under the test function
    try:
        wait_for_element(driver, By.CLASS_NAME, 'container')
        wait_for_element(driver, By.CLASS_NAME, 'menu-item') # Wait for dynamic content
        print("Menu items loaded.")
    except Exception as e:
        pytest.fail(f"FAIL - Menu items load failed on {app_url}: {e}")


    # --- Step 2: Enter Quantities and Select Discount ---
    # This section uses test_case.get() which will now work correctly
    # Ensure this loop is correctly indented under the test function
    for qty_id in qty_ids:
        qty_value = test_case.get(qty_id, '')
        if qty_value != '':
            try:
                qty_input = wait_for_element(driver, By.ID, qty_id, timeout=5)
                qty_input.clear()
                qty_input.send_keys(str(qty_value)) # Send the string value from CSV
            except Exception as e:
                pytest.fail(f"FAIL - Could not set quantity for {qty_id}: {e}")

    # Ensure this block is correctly indented under the test function
    apply_discount_str = test_case.get('ApplyDiscount', 'FALSE')
    if apply_discount_str == 'TRUE':
        try:
            discount_checkbox = wait_for_element(driver, By.ID, 'apply_discount', timeout=5)
            if not discount_checkbox.is_selected():
                 discount_checkbox.click()
            print("Applied discount checkbox.")
        except Exception as e:
             pytest.fail(f"FAIL - Could not interact with discount checkbox: {e}")

    # --- Step 3: Click Submit ---
    submit_button_locator = (By.CSS_SELECTOR, 'form button[type="submit"]')
    # Ensure this block is correctly indented under the test function
    try:
        print("Attempting to click submit button...")
        wait_and_click(driver, *submit_button_locator, timeout=5)
        print("Clicked submit button.")
        time.sleep(1.5) # Add a short delay for client-side JS/SweetAlert reaction
    except Exception as e:
         pytest.fail(f"FAIL - Could not click submit button: {e}")


    # --- Step 4: Handle Expected SweetAlerts and Page Redirect ---

    # Classify the scenario FIRST based on the *input data* using refined helpers
    # Ensure these variable assignments are correctly indented
    is_invalid_input = has_invalid_quantity_input(test_case)
    is_empty_cart = all_quantities_zero_or_empty(test_case)
    is_valid_order = has_valid_order_scenario(test_case)

    # Add basic checks to ensure scenarios are mutually exclusive (helps catch helper logic bugs)
    scenario_flags = [is_invalid_input, is_empty_cart, is_valid_order]
    if sum(scenario_flags) != 1:
        # If input doesn't fit exactly one category, it's a test data/helper logic issue
         pytest.fail(f"Internal Test Logic Error: Input data did not match exactly one expected scenario type. Invalid={is_invalid_input}, Empty={is_empty_cart}, Valid={is_valid_order}. Test Case: {test_case.get('test_id', 'N/A')}")


    # Now, execute steps based on the CLASSIFIED scenario

    # Ensure this block is correctly indented
    if is_invalid_input:
        print("Expected Scenario: Invalid Input.")
        # Expect 'Invalid Input' SweetAlert
        # Ensure blocks inside are correctly indented
        if wait_for_sweetalert(driver, "Invalid Input", timeout=10):
            print("'Invalid Input' SweetAlert appeared as expected.")
            try:
                # Expect "Yes, reset" button
                click_sweetalert_button(driver, "Yes, reset", timeout=5)
                print("Clicked 'Yes, reset'. Quantities should now be 0, remaining on menu page.")
                # Optional: Assert that the URL remained on the menu page after dismissing Swal
                current_url = driver.current_url.rstrip('/')
                expected_menu_url = app_url.rstrip('/')
                assert current_url == expected_menu_url, \
                    f"FAIL - After Invalid Input Swal and Reset, expected to remain on menu page ({expected_menu_url}) but navigated to {current_url}."
                print("Successfully remained on menu page (expected after reset).")

            except Exception as e:
                pytest.fail(f"FAIL - Error handling 'Yes, reset' after Invalid Input Swal: {e}")
        else:
            # If we classified as Invalid Input but the Swal didn't show
            pytest.fail("FAIL - Expected 'Invalid Input' SweetAlert but it did not appear within timeout or title mismatch.")

    # Ensure this block is correctly indented
    elif is_empty_cart:
        print("Expected Scenario: Empty Cart.")
        # Expect 'Empty Cart' SweetAlert and stay on menu page
        # Ensure blocks inside are correctly indented
        if wait_for_sweetalert(driver, "Empty Cart", timeout=10):
             print("'Empty Cart' SweetAlert appeared as expected.")
             try:
                 click_sweetalert_button(driver, "OK", timeout=5)
                 print("Clicked 'OK' on Empty Cart SweetAlert.")
                 time.sleep(1)

                 current_url = driver.current_url.rstrip('/')
                 expected_menu_url = app_url.rstrip('/')
                 assert current_url == expected_menu_url, \
                     f"FAIL - Expected to remain on menu page ({expected_menu_url}) but navigated to {current_url}."
                 print("Successfully remained on menu page (expected).")

                 # Optional: Assert ExpectedTotal in CSV is close to 0.00 for this scenario
                 try:
                     expected_value_clean = float(str(test_case.get('ExpectedTotal', '0.00')).strip().replace('RM', '').replace(',', ''))
                     tolerance = 0.005
                     # Use assert for direct failure on mismatch
                     assert abs(round(expected_value_clean, 2) - 0.00) < tolerance, \
                         f"FAIL - Empty Cart scenario validation failed. Expected total RM{expected_value_clean:.2f} but scenario implies 0.00."
                 except ValueError:
                      pytest.fail(f"FAIL - Invalid ExpectedTotal format in CSV for empty cart scenario: '{test_case.get('ExpectedTotal', '0.00')}'")

             except Exception as e:
                 pytest.fail(f"FAIL - Error handling Empty Cart SweetAlert or verifying page: {e}")
        else:
             # If we classified as Empty Cart but the Swal didn't show
             pytest.fail("FAIL - Expected 'Empty Cart' SweetAlert but it did not appear within timeout or title mismatch.")

    # Ensure this block is correctly indented
    elif is_valid_order:
        print("Expected Scenario: Valid Order.")
        # Expect 'Order Summary' SweetAlert and redirect to /cart page
        # Ensure blocks inside are correctly indented
        if wait_for_sweetalert(driver, "Order Summary", timeout=15): # Increased timeout for clarity
             print("'Order Summary' SweetAlert appeared as expected.")
             try:
                 click_sweetalert_button(driver, "OK", timeout=5)
                 print("Clicked 'OK' on Order Summary SweetAlert.")
                 time.sleep(1)

             except Exception as e:
                 pytest.fail(f"FAIL - Error clicking 'OK' on Order Summary SweetAlert: {e}")

             # Expect redirect to /cart page
             cart_url = app_url + "cart" # Use already joined app_url
             print(f"Waiting for page to redirect to {cart_url}")
             try:
                 WebDriverWait(driver, 10).until(EC.url_to_be(cart_url))
                 print("Successfully redirected to cart page.")
             except TimeoutException:
                 pytest.fail(f"FAIL - Did not redirect to cart page ({cart_url}) within timeout after Order Summary Swal.")
             except Exception as e:
                 pytest.fail(f"FAIL - Error waiting for redirect to cart page: {e}")

             # --- Step 5: Verify Total Summary on Cart Page ---
             print("Checking total summary on the Cart page.")
             total_element_locator = (By.CSS_SELECTOR, '.total-summary .final-total span')
             total_summary_container_locator = (By.CLASS_NAME, 'total-summary')
             cart_table_locator = (By.CLASS_NAME, 'cart-table') # Wait for main content

             # Ensure this block is correctly indented
             try:
                 # Safely get and clean expected total from CSV
                 expected_value_clean = float(str(test_case.get('ExpectedTotal', '0.00')).strip().replace('RM', '').replace(',', ''))
             except ValueError:
                  pytest.fail(f"FAIL - Invalid ExpectedTotal format in CSV: '{test_case.get('ExpectedTotal', '0.00')}'")

             # Ensure this block is correctly indented
             try:
                 # Wait for elements on the cart page
                 wait_for_element(driver, *cart_table_locator, timeout=10)
                 wait_for_element(driver, *total_summary_container_locator, timeout=5)
                 total_element = wait_for_element(driver, *total_element_locator, timeout=5)
                 computed_value_text = total_element.text.strip()

                 # Clean the text (remove RM, commas, strip whitespace) before converting to float
                 computed_numeric_str = computed_value_text.replace('RM', '').strip().replace(',', '')
                 computed_value_clean = float(computed_numeric_str)

                 print(f"Actual Computed Total (from page): RM{computed_value_clean:.2f}")
                 print(f"Expected Total (from CSV): RM{expected_value_clean:.2f}")

                 tolerance = 0.005 # Allow a small floating point tolerance
                 # Use assert for the actual test validation
                 assert abs(computed_value_clean - expected_value_clean) < tolerance, \
                     f"Assertion Failed! Expected Total: RM{expected_value_clean:.2f}, Got: RM{computed_value_clean:.2f}"
                 print("Total calculation verified (PASS)!")

             except (AssertionError, ValueError) as e:
                 pytest.fail(f"FAIL - Assertion/ValueError on cart page: {e}")
             except TimeoutException:
                 # If cart page loaded but elements didn't appear, check if empty cart state is visible
                 if is_element_present(driver, (By.XPATH, "//div[@class='container']/p[contains(text(), 'Your cart is empty')]"), timeout=2):
                      pytest.fail(f"FAIL - Expected total summary on cart page but found empty cart message unexpectedly.")
                 else:
                     pytest.fail(f"FAIL - Timeout waiting for total summary element on cart page.")
             except Exception as e:
                  pytest.fail(f"FAIL - An unexpected error occurred during total comparison on cart page: {e}")

        else:
             # If we classified as Valid Order but the Order Summary Swal didn't show
             pytest.fail("FAIL - Expected 'Order Summary' SweetAlert but it did not appear within timeout or title mismatch.")

    # This final 'else' block is the fallback for any case that wasn't classified
    # It indicates an issue with the test data or classification logic.
    # Ensure this 'else' is at the correct indentation level relative to the preceding 'if' and 'elif' blocks.
    else:
         # This case should ideally not be reached if scenarios cover all possibilities
         # It might indicate a logic error in the test script itself or an unexpected application behavior
         # Fail explicitly as the input didn't fit known scenarios.
         pytest.fail(f"FAIL - Input data ({test_case}) did not fit into 'Invalid Input', 'Empty Cart', or 'Valid Order' scenario classification.")