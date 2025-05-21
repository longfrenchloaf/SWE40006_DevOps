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

        # Use dtype=str to read everything as strings initially, preserving exact input.
        # 'comment' ignores lines starting with #
        df = pd.read_csv(csv_filepath, dtype=str, comment='#')

        data = []
        # Use iterrows for easier access to index and row data
        for index, row in df.iterrows():
             # Convert row to dictionary, handling potential NaN (missing values)
             # Fill NaN with empty strings or a placeholder that to_dict handles appropriately
             test_case = row.fillna('').to_dict() # Fill NaN with empty strings

             # Clean up quantity values - ensure they are strings with leading/trailing space removed
             for i in range(8):
                 key = f'qty_{i}'
                 # Get the value, strip whitespace. It's already a string from dtype=str.
                 qty_value_str = test_case.get(key, '').strip()

                 # Store the cleaned string back
                 test_case[key] = qty_value_str

             # Standardize discount to uppercase string, strip whitespace
             test_case['ApplyDiscount'] = test_case.get('ApplyDiscount', '').upper().strip()

             # Add a unique identifier using the index
             test_case['test_id'] = f"case_{index + 1}"

             data.append(test_case)

        if not data:
             print(f"Warning: No test cases found in {filename} after reading or all were comments/empty.")

        return data
    except FileNotFoundError:
        # Use pytest.fail here as it's a critical setup failure
        pytest.fail(f"Test case CSV not found at {filename}. Please check the path: {csv_filepath}")
    except Exception as e:
        # Use pytest.fail here as it's a critical setup failure
        pytest.fail(f"Error reading or processing CSV file {filename} at {csv_filepath}: {e}")


# --- Refined Helper Functions for Scenario Classification ---
# These helpers MUST match the JS validation logic in validateInput()

def is_valid_positive_integer_string(qty_str):
    """Checks if a string is composed only of digits (>= 0 integer) matching JS /^\d+$/."""
    if qty_str is None or qty_str.strip() == '':
        return False # Empty string is treated as 0 quantity *after* format check, but not a valid *input format* for this specific check according to the JS regex !/^\d+$/.
    # JS regex /^\d+$/ checks if the *entire* string consists of one or more digits.
    return qty_str.strip().isdigit() # isdigit() does exactly this for non-empty strings.

def has_invalid_quantity_input(test_case):
    """Checks if any quantity input string would trigger the 'Invalid Input' SweetAlert."""
    qty_ids = [f'qty_{i}' for i in range(8)]
    for qty_id in qty_ids:
        qty_value = test_case.get(qty_id, '').strip()
        # JS logic: if val is not empty AND doesn't match /^\d+$/
        if qty_value != "" and not is_valid_positive_integer_string(qty_value):
             print(f"Classification check: Found invalid input '{qty_value}' for {qty_id}") # Debugging
             return True
    print("Classification check: No invalid input formats found.") # Debugging
    return False # No quantity input string failed the JS format check

def all_quantities_zero_or_empty(test_case):
    """Checks if all quantity inputs are effectively zero (empty string or '0')
       *after* assuming invalid inputs are ignored or handled (like being reset to 0).
       This helper reflects the *second* stage of JS validation."""
    qty_ids = [f'qty_{i}' for i in range(8)]
    has_any_positive_valid_qty = False
    for qty_id in qty_ids:
        qty_value = test_case.get(qty_id, '').strip()

        # We only care about quantities that *would be* valid according to the JS format check.
        # Invalidly formatted inputs are handled FIRST by the JS.
        # If the input is a valid digit string AND is greater than "0"
        if qty_value != "" and qty_value.isdigit() and int(qty_value) > 0:
             has_any_positive_valid_qty = True
             break # Found at least one non-zero valid quantity

    # It's an 'Empty Cart' scenario *in the second validation stage* if there are NO positive valid quantities
    print(f"Classification check: all_quantities_zero_or_empty returned {not has_any_positive_valid_qty}") # Debugging
    return not has_any_positive_valid_qty

# We will determine the final scenario classification within the test function
# based on the sequence of JS checks using the above helpers.


# --- Fixture for Test Data Loading and Parameterization ---
@pytest.fixture(scope="module", params=read_csv_data('test_cases.csv'), ids=lambda test_case: test_case.get('test_id', 'unknown_id'))
def test_case(request):
    """Pytest fixture to load and parameterize test data from CSV."""
    return request.param

# --- Fixture for WebDriver Setup ---
@pytest.fixture(scope="module") # Use module scope for efficiency unless isolation per test is strictly needed
def driver():
    """Pytest fixture to set up and tear down the Selenium WebDriver."""
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--headless') # UNCOMMENT this for CI/headless execution (no visible browser window)
    # options.add_argument('--disable-gpu') # Might be needed for headless on some systems
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    # options.add_argument('--ignore-certificate-errors') # Use with caution

    print("\nSetting up browser...")
    driver = webdriver.Chrome(options=options)
    yield driver
    print("\nClosing browser...")
    driver.quit()


# --- Helper functions (wait_for_element, etc.) ---

def wait_for_element(driver, by, value, timeout=10):
   """Waits for an element to be present on the page and returns it."""
   try:
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
        WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        ).click()
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
        # print(f"Warning: Error checking for element presence ({by}={value}): {e}") # Optional debug
        return False

def wait_for_sweetalert(driver, title_substring, timeout=10):
    """Waits for a SweetAlert modal with a title containing a specific substring."""
    try:
        # Wait for the modal container to be visible
        WebDriverWait(driver, timeout).until(
             EC.visibility_of_element_located((By.CLASS_NAME, 'swal2-container'))
        )
        # Then wait for the actual popup and its title within the container
        popup = WebDriverWait(driver, timeout=2).until(
             EC.visibility_of_element_located((By.CLASS_NAME, 'swal2-popup'))
        )
        title_element = WebDriverWait(popup, timeout=2).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.swal2-title'))
        )
        detected_title = title_element.text.strip()
        print(f"Detected SweetAlert with title: '{detected_title}' (Looking for substring: '{title_substring}')")
        return title_substring in detected_title

    except TimeoutException:
        print(f"Timeout waiting for SweetAlert with title substring '{title_substring}'. No Swal or incorrect title.")
        return False
    except Exception as e:
         pytest.fail(f"Error waiting for SweetAlert with title substring '{title_substring}': {e}")


def click_sweetalert_button(driver, text, timeout=5):
    """Clicks a SweetAlert button containing specific text."""
    button_locator = (By.XPATH, f"//button[contains(@class, 'swal2') and contains(text(), '{text}')]")
    try:
        wait_and_click(driver, *button_locator, timeout=timeout)
        print(f"Clicked SweetAlert button with text: '{text}'.")
    except Exception as e:
         pytest.fail(f"Failed to click SweetAlert button with text '{text}': {e}")


# --- Main Pytest Test Function ---
def test_food_billing_scenario(driver, test_case):
    """Tests a food billing scenario based on CSV data."""
    # 'test_case' is the dictionary provided by the parameterized fixture.
    # Access CSV data using test_case.get('column_name', default_value).
    # Use pytest.fail() or assertions to indicate test failure.

    # Get the application URL from an environment variable or use default
    app_url = os.environ.get("APP_URL", "http://4.206.70.73:5000/")
    if not app_url.endswith('/'):
        app_url += '/'

    # Print test case details for debugging
    qty_ids = [f'qty_{i}' for i in range(8)]
    qty_details = [f'{f}: "{test_case.get(f, "")}"' for f in qty_ids]
    print(f"\n--- Executing Test Case: {test_case.get('test_id', 'N/A')} ---")
    print(f"Details: Quantities=[{', '.join(qty_details)}], Discount={test_case.get('ApplyDiscount', 'FALSE')}, ExpectedTotal={test_case.get('ExpectedTotal', 'N/A')}")
    print(f"Target URL: {app_url}")


    # --- Step 1: Navigate to Menu Page ---
    try:
        driver.get(app_url)
        print(f"Navigated to menu page: {app_url}")
    except Exception as e:
         pytest.fail(f"FAIL - Navigation failed to {app_url}: {e}")

    try:
        wait_for_element(driver, By.CLASS_NAME, 'container')
        wait_for_element(driver, By.CLASS_NAME, 'menu-item')
        print("Menu items container and at least one item loaded.")
    except Exception as e:
        if is_element_present(driver, (By.XPATH, "//p[contains(text(), 'Unable to load menu items.')]"), timeout=2):
             pytest.fail("FAIL - Detected 'Unable to load menu items' error message on the page.")
        else:
             pytest.fail(f"FAIL - Menu items load failed on {app_url}: {e}")


    # --- Step 2: Enter Quantities and Select Discount ---
    for qty_id in qty_ids:
        qty_value = test_case.get(qty_id, '').strip()
        try:
            qty_input = wait_for_element(driver, By.ID, qty_id, timeout=5)
            qty_input.clear() # Always clear before sending keys
            qty_input.send_keys(qty_value) # Send the string value from CSV
            print(f"Set quantity for {qty_id} to '{qty_value}'")
        except Exception as e:
            pytest.fail(f"FAIL - Could not set quantity for {qty_id}: {e}")

    apply_discount_str = test_case.get('ApplyDiscount', 'FALSE')
    try:
        discount_checkbox = wait_for_element(driver, By.ID, 'apply_discount', timeout=5)
        if apply_discount_str == 'TRUE':
            if not discount_checkbox.is_selected():
                 discount_checkbox.click()
            print("Applied discount checkbox.")
        else: # Handle FALSE explicitly to ensure it's off
            if discount_checkbox.is_selected():
                 discount_checkbox.click()
            print("Ensured discount checkbox is NOT applied.")
    except Exception as e:
         pytest.fail(f"FAIL - Could not interact with discount checkbox: {e}")


    # --- Step 3: Click Submit ---
    submit_button_locator = (By.CSS_SELECTOR, 'form button[type="submit"]')
    try:
        print("Attempting to click submit button...")
        wait_and_click(driver, *submit_button_locator, timeout=5)
        print("Clicked submit button.")
        time.sleep(0.5) # Allow JS to start validation and show Swal if needed
    except Exception as e:
         pytest.fail(f"FAIL - Could not click submit button: {e}")


    # --- Step 4: Handle Expected SweetAlerts and Page Redirect ---

    # Classify the scenario based on the *input data* and the *sequence* of JS checks.
    is_invalid_input = has_invalid_quantity_input(test_case)
    # The empty cart check only happens IF there's no invalid input format.
    # We need to check the state *after* potential reset for invalid cases.
    # The all_quantities_zero_or_empty helper correctly determines if, considering
    # only the *valid digit strings*, all quantities are effectively zero.
    # This helper implicitly reflects the state *after* invalid inputs are ignored or reset.
    is_empty_cart_after_format_check = all_quantities_zero_or_empty(test_case)
    # A valid order happens if no invalid format AND at least one valid quantity > 0
    is_valid_order_after_checks = not is_invalid_input and not is_empty_cart_after_format_check

    # --- Determine the *expected* sequence of Swals/actions ---
    if is_invalid_input:
        expected_first_swal = "Invalid Input"
        # After clicking "Yes, reset", the JS re-validates.
        # If all *valid* quantities were 0 or empty, it becomes an Empty Cart scenario.
        # If any *valid* quantity was > 0, it becomes a Valid Order scenario.
        if all_quantities_zero_or_empty(test_case):
            expected_second_swal = "Empty Cart"
            expected_final_action = "Stay on Menu" # After OK on Empty Cart
        else:
            expected_second_swal = "Order Summary"
            expected_final_action = "Redirect to Cart" # After View Order Details on Order Summary
    elif all_quantities_zero_or_empty(test_case): # This only runs if !is_invalid_input
        expected_first_swal = "Empty Cart"
        expected_second_swal = None # No second Swal expected
        expected_final_action = "Stay on Menu"
    else: # This only runs if !is_invalid_input and !all_quantities_zero_or_empty
        expected_first_swal = "Order Summary"
        expected_second_swal = None # No second Swal expected
        expected_final_action = "Redirect to Cart"

    print(f"Expected Flow: First Swal: '{expected_first_swal}'")
    if expected_second_swal:
        print(f"               Second Swal (after reset): '{expected_second_swal}'")
    print(f"               Final Action: '{expected_final_action}'")


    # --- Step 4a: Handle the First Expected SweetAlert ---
    detected_first_swal_title = None
    if wait_for_sweetalert(driver, expected_first_swal, timeout=15): # Use longer timeout for first Swal
        print(f"First SweetAlert ('{expected_first_swal}') appeared as expected.")
        detected_first_swal_title = expected_first_swal
    else:
        pytest.fail(f"FAIL - Expected first SweetAlert '{expected_first_swal}' but it did not appear within timeout or title mismatch.")

    # --- Step 4b: Perform action based on the first Swal ---
    if detected_first_swal_title == "Invalid Input":
        try:
            # Click "Yes, reset". This triggers recursive validation in JS.
            click_sweetalert_button(driver, "Yes, reset", timeout=5)
            print("Clicked 'Yes, reset'. Expecting re-validation and second Swal.")
            time.sleep(0.5) # Allow JS re-validation and potential second Swal
        except Exception as e:
            pytest.fail(f"FAIL - Error clicking 'Yes, reset' button on '{detected_first_swal_title}' Swal: {e}")

        # --- Step 4c (for Invalid Input path): Handle the Second Expected SweetAlert ---
        detected_second_swal_title = None
        if wait_for_sweetalert(driver, expected_second_swal, timeout=10): # Shorter timeout for second Swal
             print(f"Second SweetAlert ('{expected_second_swal}') appeared as expected after reset.")
             detected_second_swal_title = expected_second_swal
        else:
             pytest.fail(f"FAIL - Expected second SweetAlert '{expected_second_swal}' after reset, but it did not appear within timeout or title mismatch.")

        # Now handle the button click for the second Swal
        if detected_second_swal_title == "Empty Cart":
            try:
                click_sweetalert_button(driver, "OK", timeout=5)
                print("Clicked 'OK' on 'Empty Cart' SweetAlert.")
                time.sleep(0.5)
            except Exception as e:
                 pytest.fail(f"FAIL - Error clicking 'OK' button on 'Empty Cart' Swal: {e}")
        elif detected_second_swal_title == "Order Summary":
             try:
                 click_sweetalert_button(driver, "View Order Details", timeout=5)
                 print("Clicked 'View Order Details' on 'Order Summary' SweetAlert.")
                 time.sleep(0.5)
             except Exception as e:
                 pytest.fail(f"FAIL - Error clicking 'View Order Details' button on 'Order Summary' Swal: {e}")
        else:
             # This case should not be reached if expected_second_swal was correctly one of these
             pytest.fail(f"Internal Test Logic Error: Unexpected second Swal title '{detected_second_swal_title}' after Invalid Input reset.")


    elif detected_first_swal_title == "Empty Cart":
         try:
             click_sweetalert_button(driver, "OK", timeout=5)
             print("Clicked 'OK' on 'Empty Cart' SweetAlert.")
             time.sleep(0.5)
         except Exception as e:
             pytest.fail(f"FAIL - Error clicking 'OK' button on 'Empty Cart' Swal: {e}")

    elif detected_first_swal_title == "Order Summary":
         try:
             click_sweetalert_button(driver, "View Order Details", timeout=5)
             print("Clicked 'View Order Details' on 'Order Summary' SweetAlert.")
             time.sleep(0.5)
         except Exception as e:
             pytest.fail(f"FAIL - Error clicking 'View Order Details' button on 'Order Summary' Swal: {e}")

    else:
         # This case should not be reached if detected_first_swal_title was set correctly
         pytest.fail(f"Internal Test Logic Error: Unhandled first Swal title '{detected_first_swal_title}'.")

    # --- Step 4d: Verify the Final Action (Stay on Menu or Redirect to Cart) ---
    if expected_final_action == "Stay on Menu":
         current_url = driver.current_url.rstrip('/')
         expected_menu_url = app_url.rstrip('/')
         assert current_url == expected_menu_url, \
             f"FAIL - Expected to remain on menu page ({expected_menu_url}) but navigated to {current_url}."
         print("Successfully remained on menu page (expected).")

         # For Stay on Menu, the ExpectedTotal from CSV must be 0.00
         try:
             expected_value_str = str(test_case.get('ExpectedTotal', '0.00')).strip().replace('RM', '').replace(',', '')
             expected_value_clean = float(expected_value_str) if expected_value_str else 0.00

             tolerance = 0.005
             assert abs(round(expected_value_clean, 2) - 0.00) < tolerance, \
                 f"FAIL - ExpectedTotal mismatch for Stay on Menu scenario. Expected total RM{expected_value_clean:.2f} from CSV but scenario implies 0.00."
             print("Expected total of 0.00 correctly linked to this Stay on Menu scenario.")
         except ValueError:
              pytest.fail(f"FAIL - Invalid ExpectedTotal format in CSV for Stay on Menu scenario: '{test_case.get('ExpectedTotal', '0.00')}'")

    elif expected_final_action == "Redirect to Cart":
         cart_url = app_url + "cart"
         print(f"Waiting for page to redirect to {cart_url}")
         try:
             WebDriverWait(driver, 10).until(EC.url_to_be(cart_url))
             print("Successfully redirected to cart page.")
         except TimeoutException:
             pytest.fail(f"FAIL - Did not redirect to cart page ({cart_url}) within timeout after Order Summary Swal.")
         except Exception as e:
             pytest.fail(f"FAIL - Error waiting for redirect to cart page: {e}")

         # --- Step 5: Verify Final Total Summary on Cart Page (Only for Redirect to Cart) ---
         print("Checking final total summary on the Cart page.")
         total_element_locator = (By.CSS_SELECTOR, '.total-summary .final-total span')
         total_summary_container_locator = (By.CLASS_NAME, 'total-summary')
         cart_table_locator = (By.CLASS_NAME, 'cart-table')

         try:
             # Safely get and clean expected total from CSV
             expected_value_str = str(test_case.get('ExpectedTotal', '0.00')).strip().replace('RM', '').replace(',', '')
             expected_value_clean = float(expected_value_str) if expected_value_str else 0.00
         except ValueError:
              pytest.fail(f"FAIL - Invalid ExpectedTotal format in CSV: '{test_case.get('ExpectedTotal', '0.00')}'")

         try:
             wait_for_element(driver, *cart_table_locator, timeout=10)
             wait_for_element(driver, *total_summary_container_locator, timeout=5)
             total_element = wait_for_element(driver, *total_element_locator, timeout=5)
             computed_value_text = total_element.text.strip()

             computed_numeric_str = computed_value_text.replace('RM', '').strip().replace(',', '')
             computed_value_clean = float(computed_numeric_str)

             print(f"Actual Computed Total (from Cart page): RM{computed_value_clean:.2f}")
             print(f"Expected Final Total (from CSV): RM{expected_value_clean:.2f}")

             tolerance = 0.01
             assert abs(round(computed_value_clean, 2) - round(expected_value_clean, 2)) < tolerance, \
                 f"Assertion Failed! Expected Final Total: RM{expected_value_clean:.2f}, Got: RM{computed_value_clean:.2f}"
             print("Final Total calculation verified on Cart page (PASS)!")

         except (AssertionError, ValueError) as e:
             pytest.fail(f"FAIL - Assertion/ValueError on cart page: {e}")
         except TimeoutException:
             if is_element_present(driver, (By.XPATH, "//div[@class='container']/p[contains(text(), 'Your cart is empty')]"), timeout=2):
                  pytest.fail(f"FAIL - Expected total summary on cart page but found empty cart message unexpectedly after valid order scenario.")
             else:
                 pytest.fail(f"FAIL - Timeout waiting for total summary element on cart page.")
         except Exception as e:
              pytest.fail(f"FAIL - An unexpected error occurred during total comparison on cart page: {e}")

    else:
         pytest.fail(f"Internal Test Logic Error: Unhandled final action '{expected_final_action}'.")