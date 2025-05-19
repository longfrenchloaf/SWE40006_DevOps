<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"/>
    <meta name="description" content="Cafe Menu"/>
    <meta name="keywords" content="cafe, menu, coffee, tea, matcha, pastry, online order"/>
    <meta name="author" content="Your Name"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Our Cozy Cafe Menu</title>
    <link rel="stylesheet" href="style.css"> <!-- Link to the EXTERNAL CSS file -->
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
</head>

<body>
    <?php
    // Define menu items using an array - CAFE MENU & NEW PRICES/IMAGES (Same as previous)
    $items = [
        ['id' => 'latte', 'name' => 'Latte', 'price' => 8.00, 'image' => 'Latte.jpg'],
        ['id' => 'cappuccino', 'name' => 'Cappuccino', 'price' => 8.00, 'image' => 'Cappuccino.jpg'],
        ['id' => 'matchalatte', 'name' => 'Matcha Latte', 'price' => 10.00, 'image' => 'MatchaLatte.jpg'],
        ['id' => 'icedamericano', 'name' => 'Iced Americano', 'price' => 7.00, 'image' => 'IcedAmericano.jpg'],
        ['id' => 'hotchocolate', 'name' => 'Hot Chocolate', 'price' => 7.50, 'image' => 'HotChocolate.jpg'],
        ['id' => 'croissant', 'name' => 'Butter Croissant', 'price' => 5.00, 'image' => 'Croissant.jpg'],
        ['id' => 'blueberrymuffin', 'name' => 'Blueberry Muffin', 'price' => 6.50, 'image' => 'BlueberryMuffin.jpg'],
        ['id' => 'icedpeachtea', 'name' => 'Iced Peach Tea', 'price' => 5.50, 'image' => 'IcedPeachTea.jpg'],
    ];

    // Discount percentage
    $discount_percentage = 50;
    ?>

    <h2>Cafe Tralalelo Tralala</h2>

    <div class="container"> <!-- Wrap content in the container -->
        <form action="cart.php" method="post" onsubmit="return validateInput(event)">

            <!-- NEW MENU LAYOUT STRUCTURE -->
            <div class="menu-layout">
                <?php foreach ($items as $index => $item): ?>
                    <div class="menu-item">
                        <img src="<?php echo htmlspecialchars($item['image']); ?>" alt="<?php echo htmlspecialchars($item['name']); ?>">
                        <div class="item-details"> <!-- Wrapper for text and input -->
                            <h4><?php echo htmlspecialchars($item['name']); ?></h4>
                            <p class="price">RM<?php echo number_format($item['price'], 2); ?></p>
                             <div class="quantity-input">
                                <label for="qty_<?php echo $index; ?>">Quantity:</label> <!-- Optional label -->
                                <input type="number" id="qty_<?php echo $index; ?>" name="qty_<?php echo $index; ?>" value="0" min="0" title="Enter a positive whole number">
                             </div>
                        </div>
                    </div>
                <?php endforeach; ?>
            </div>
            <!-- END NEW MENU LAYOUT STRUCTURE -->

            <div class="discount-container">
                <input type="checkbox" name="apply_discount" id="apply_discount" value="yes">
                <label for="apply_discount">Apply <?php echo $discount_percentage; ?>% Special Discount</label>
            </div>

            <button name="submit_button" type="submit">Add to Cart</button>
        </form>
    </div>

    <!-- SweetAlert2 validation script -->
    <script type="text/javascript">
    async function validateInput(event) {
        const inputs = document.querySelectorAll('input[type="number"]');
        const integerPattern = /^[0-9]+$/;
        let invalidFields = [];
        let invalidNames = [];
        let hasQuantity = false;

        for (let input of inputs) {
            const value = input.value.trim();
            const quantity = parseInt(value, 10);

            if (value !== "" && (!integerPattern.test(value) || quantity < 0)) {
                 invalidFields.push(input);
                 // Find the item name - now h4 instead of td.text-left
                 const itemDiv = input.closest('.menu-item');
                 const itemName = itemDiv ? itemDiv.querySelector('h4').textContent.trim() : input.name;
                 invalidNames.push(itemName);
            }

            if (quantity > 0) {
                hasQuantity = true;
            }
        }

        if (invalidFields.length > 0) {
            const invalidNamesText = invalidNames.join(', ');

            const result = await Swal.fire({
                title: 'Invalid Input',
                html: `<p>Please enter positive whole numbers for quantity.</p><p>The following items have invalid quantities: <strong>${invalidNamesText}</strong>.</p>Do you want to reset these to 0 and continue?`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Yes, reset to 0',
                cancelButtonText: 'No, correct manually',
                customClass: {
                    popup: 'swal2-popup',
                    backdrop: 'swal2-backdrop'
                },
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            if (result.isConfirmed) {
                invalidFields.forEach(input => {
                    input.value = '0';
                });
                 let recheckHasQuantity = false;
                 document.querySelectorAll('input[type="number"]').forEach(input => {
                     if (parseInt(input.value, 10) > 0) {
                         recheckHasQuantity = true;
                     }
                 });
                if (recheckHasQuantity) {
                    return true;
                } else {
                     Swal.fire({
                         title: 'Cart Empty',
                         text: 'All quantities were reset to 0. Please add items to order.',
                         icon: 'info',
                         confirmButtonText: 'OK'
                     });
                     return false;
                }

            } else {
                invalidFields.forEach(input => {
                     input.style.borderColor = 'red';
                });
                return false;
            }
        } else if (!hasQuantity) {
            Swal.fire({
                title: 'Cart Empty',
                text: 'Please add at least one item to your cart.',
                icon: 'info',
                confirmButtonText: 'OK'
            });
            return false;
        } else {
            return true;
        }
    }
    </script>

</body>
</html>