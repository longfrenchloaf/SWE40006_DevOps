<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"/>
    <meta name="description" content="Cafe Order Summary"/>
    <meta name="keywords" content="cafe, order, summary, bill, coffee, tea, matcha"/>
    <meta name="author" content="Your Name"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cafe Order Summary</title>
    <link rel="stylesheet" href="style.css"> <!-- Link to the EXTERNAL CSS file -->
</head>

<body>
    <?php
    // Define menu items (must match menu.php) - CAFE MENU & NEW PRICES/IMAGES
     $items = [
        ['id' => 'latte', 'name' => 'Latte', 'price' => 8.00, 'image' => 'images/Latte.jpg'],
        ['id' => 'cappuccino', 'name' => 'Cappuccino', 'price' => 8.00, 'image' => 'images/Cappuccino.jpg'],
        ['id' => 'matchalatte', 'name' => 'Matcha Latte', 'price' => 10.00, 'image' => 'images/MatchaLatte.jpg'],
        ['id' => 'icedamericano', 'name' => 'Iced Americano', 'price' => 7.00, 'image' => 'images/IcedAmericano.jpg'],
        ['id' => 'hotchocolate', 'name' => 'Hot Chocolate', 'price' => 7.50, 'image' => 'images/HotChocolate.jpg'],
        ['id' => 'croissant', 'name' => 'Butter Croissant', 'price' => 5.00, 'image' => 'images/Croissant.jpg'],
        ['id' => 'blueberrymuffin', 'name' => 'Blueberry Muffin', 'price' => 6.50, 'image' => 'images/BlueberryMuffin.jpg'],
        ['id' => 'icedpeachtea', 'name' => 'Iced Peach Tea', 'price' => 5.50, 'image' => 'images/IcedPeachTea.jpg'],
    ];

    // Discount and SST percentages
    $discount_percentage = 50;
    $sst_percentage = 6;

    $subtotal_before_discount = 0;
    $ordered_items = []; // Array to store items with quantity > 0

    // Process quantities from POST data
    foreach ($items as $index => $item) {
        $quantity = filter_input(INPUT_POST, 'qty_' . $index, FILTER_VALIDATE_INT);

        if ($quantity === false || $quantity === null || $quantity < 0) {
            $quantity = 0;
        }

        if ($quantity > 0) {
            $item_subtotal = $quantity * $item['price'];
            $subtotal_before_discount += $item_subtotal;

            // Store details for display
            $ordered_items[] = [
                'name' => $item['name'],
                'price' => $item['price'],
                'image' => $item['image'],
                'quantity' => $quantity,
                'subtotal' => $item_subtotal
            ];
        }
    }

    $discount_amount = 0;
    $subtotal_after_discount = $subtotal_before_discount;

    // Apply discount if checkbox was checked
    $apply_discount = isset($_POST['apply_discount']) && $_POST['apply_discount'] === 'yes';
    if ($apply_discount) {
        $discount_amount = $subtotal_before_discount * ($discount_percentage / 100);
        $subtotal_after_discount = $subtotal_before_discount - $discount_amount;
        if ($subtotal_after_discount < 0) {
             $subtotal_after_discount = 0;
             $discount_amount = $subtotal_before_discount;
        }
    }

    // Calculate SST
    $sst_amount = $subtotal_after_discount * ($sst_percentage / 100);

    // Calculate Final Total
    $final_total = $subtotal_after_discount + $sst_amount;
    ?>

    <h2>Order Summary</h2>

    <div class="container"> <!-- Wrap content in the container -->
        <?php if (empty($ordered_items)): ?>
            <p>Your cart is empty. Please add items from the <a href="menu.php">menu</a>.</p>
        <?php else: ?>
            <!-- Added class="cart-table" here -->
            <table class="cart-table">
                <thead>
                    <tr>
                        <th>Image</th>
                        <th class="text-left">Name</th>
                        <th class="text-right">Price (RM)</th>
                        <th>Quantity</th>
                        <th class="text-right">Subtotal (RM)</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($ordered_items as $item): ?>
                    <tr>
                        <td data-label="Image"><img src="<?php echo htmlspecialchars($item['image']); ?>" alt="<?php echo htmlspecialchars($item['name']); ?>"></td>
                        <td data-label="Name" class="text-left"><?php echo htmlspecialchars($item['name']); ?></td>
                        <td data-label="Price (RM)" class="text-right"><?php echo number_format($item['price'], 2); ?></td>
                        <td data-label="Quantity"><?php echo $item['quantity']; ?></td>
                        <td data-label="Subtotal (RM)" class="text-right"><?php echo number_format($item['subtotal'], 2); ?></td>
                    </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>

            <div class="total-summary">
                <div>
                    <strong>Subtotal:</strong> <span>RM<?php echo number_format($subtotal_before_discount, 2); ?></span>
                </div>
                 <?php if ($apply_discount): ?>
                 <div>
                    <strong>Discount (<?php echo $discount_percentage; ?>%):</strong> <span>-RM<?php echo number_format($discount_amount, 2); ?></span>
                 </div>
                 <div>
                    <strong>Subtotal (after discount):</strong> <span>RM<?php echo number_format($subtotal_after_discount, 2); ?></span>
                 </div>
                 <?php endif; ?>
                 <div>
                    <strong>SST (<?php echo $sst_percentage; ?>%):</strong> <span>RM<?php echo number_format($sst_amount, 2); ?></span>
                 </div>
                <div class="final-total">
                    <strong>Total to Pay:</strong> <span>RM<?php echo number_format($final_total, 2); ?></span>
                </div>
            </div>
        <?php endif; ?>

         <a href="menu.php" class="back-button">Go Back to Menu</a> <!-- This link gets the new .back-button style -->

    </div>

</body>
</html>