CREATE TABLE menu_items (
id SERIAL PRIMARY KEY,
name VARCHAR(255) NOT NULL,
price DECIMAL(10, 2) NOT NULL,
image VARCHAR(255)
);

INSERT INTO menu_items (name, price, image) VALUES
('Latte', 8.00, 'Latte.jpg'),
('Cappuccino', 8.00, 'Cappuccino.jpg'),
('Matcha Latte', 10.00, 'MatchaLatte.jpg'),
('Iced Americano', 7.00, 'IcedAmericano.jpg'),
('Hot Chocolate', 7.50, 'HotChocolate.jpg'),
('Butter Croissant', 5.00, 'Croissant.jpg'),
('Blueberry Muffin', 6.50, 'BlueberryMuffin.jpg'),
('Iced Peach Tea', 5.50, 'IcedPeachTea.jpg');