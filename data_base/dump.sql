DROP DATABASE IF EXISTS neurofood;
CREATE DATABASE neurofood;
USE neurofood;

/* Краткое описание:
 * База данных - маркетплейс для бота в телеграм. Предназначена для хранения информации о пользователях, партнерах, 
 * товарах и т.д. Данная БД предоставляет возможность осуществлять торговые операции между пользователями прямо в месседжере.
 */
																		    # * - поля заполняющиеся по умолчанию програмно
# Таблица users заполняется по мере ввода информации пользователем
DROP TABLE IF EXISTS users;
CREATE TABLE users (
	id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT UNIQUE PRIMARY KEY, 			# Идентификатор пользователя в телеграм*
	login VARCHAR(100) NOT NULL,      										# Username пользователя в телеграм*
	fullname VARCHAR(255),													# Полное имя пользователя
	phone BIGINT,															# Телефон
	address VARCHAR(255),													# Адрес
	created_at timestamp DEFAULT NOW()										# Дата входа 
) COMMENT 'Пользователи';

# Индекс для ускореного поиска пользователя по логину
CREATE INDEX login_index ON users(login) USING BTREE;

# Таблица describes содержит информацию с описанием позиции в таблице product
DROP TABLE IF EXISTS describes;
CREATE TABLE describes(
	id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT UNIQUE PRIMARY KEY,  		# Идентификатор
	product_name VARCHAR(100),												# Название товара
	img_address TEXT,														# id изображения в телеграм
	description TEXT														# Описание товара
) COMMENT 'Описание товаров';

#Таблица-справочник с названием доступных форм (Жидкость\Концетрат и т.д.)
DROP TABLE IF EXISTS forms;
CREATE TABLE forms (
	id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT UNIQUE PRIMARY KEY,			# Идентификатор
	form_name VARCHAR (100)													# Наименование формы
) COMMENT 'Справочник форм товара';

# Позиции, подтвержденные администратором через процедуру application_approve
DROP TABLE IF EXISTS products;
CREATE TABLE products (
	id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,				    # Идентификатор(для удобства в сложных запросах)
	describe_id BIGINT UNSIGNED NOT NULL,									# Ссылка на описание
	weight BIGINT UNSIGNED NOT NULL,										# Вес в граммах
	form_id BIGINT UNSIGNED NOT NULL,										# Ссылка на справочник форм
	price DECIMAL(25, 2),													# Цена (Может быть null)
	UNIQUE(describe_id, weight, form_id),	    							# Не входят в PK, но должны быть уникальными
	FOREIGN KEY(describe_id) REFERENCES describes(id) ON UPDATE CASCADE ON DELETE CASCADE,
	FOREIGN KEY(form_id) REFERENCES forms(id) ON UPDATE CASCADE ON DELETE CASCADE
) COMMENT 'Товары';

#Заказы всех пользователей 
DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
	id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT UNIQUE PRIMARY KEY,			# Идентификатор
	user_id BIGINT UNSIGNED NOT NULL,										# Ссылка на пользователя
	product_id BIGINT UNSIGNED NOT NULL,									# Ссылка на позицию
	`status` ENUM(															# Статус заказа
			'Ожидает оплаты', 		 # Ожидается поступление оплаты за заказ. 
			'Оплачен', 				 # средства за заказ получены и после проверки менеджером заказ будет подтвержден. 
			'Подтвержден (в работе)',# оплата за заказ получена. Заказ подтвержден менеджером и передан в работу. 
			'Выполнен',				 # заказ доставлен Получателю
			'Аннулирован'			 # статус присваивается заказам которые не были оплачены или если Клиент отменил заказ.
			) DEFAULT 'Ожидает оплаты',
	FOREIGN KEY(user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
	FOREIGN KEY(product_id) REFERENCES products(id) ON UPDATE CASCADE ON DELETE CASCADE
) COMMENT 'Заказы'; 

# Таблица продавцов, которые могут подавать заявки на размещение товарной позиции
DROP TABLE IF EXISTS sellers;
CREATE TABLE sellers (													
	user_id BIGINT UNSIGNED NOT NULL PRIMARY KEY,							# Ссылка на пользователя
	token TEXT,																# Токен для подключения к интерфейсу
	pwd_hash VARCHAR(32),													# Хэш пользовательского паролья в md5
	pay_number BIGINT,														# Номер к которому привязан счет
	bank_name VARCHAR(100),													# Банк получателя
	FOREIGN KEY(user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE
) COMMENT 'Продавцы';

# Таблица связи между продовцами и товарами
DROP TABLE IF EXISTS sellers_x_product;
CREATE TABLE sellers_x_product (
	user_id BIGINT UNSIGNED NOT NULL,										# Ссылка на пользователя
	product_id BIGINT UNSIGNED NOT NULL,									# Ссылка на товар
	PRIMARY KEY(user_id, product_id),
	FOREIGN KEY(user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
	FOREIGN KEY(product_id) REFERENCES products(id) ON UPDATE CASCADE ON DELETE CASCADE
	) COMMENT 'Таблица связей между продавцом и товаром';

# Вопросы пользователей в техподдержку
DROP TABLE IF EXISTS questions;
CREATE TABLE questions (
	id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT UNIQUE PRIMARY KEY,					# Идентификатор
	user_id BIGINT UNSIGNED NOT NULL,												# Ссылка на пользователя
	question TEXT,																	# Вопрос пользователя
	status ENUM(
		'На рассмотрении', 
		'В работе', 
		'Решен', 
		'Отклонен') DEFAULT 'На рассмотрении',										# Статус
	FOREIGN KEY(user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE
) COMMENT 'Вопросы пользователей';

/* Заявки продавцов на добавление товарной позиции, заполняется продавцом через интерфейс.
   Администратор имеет право редактировать заявку, если, например обнаружит ошибку в форме товара. */
DROP TABLE IF EXISTS applications;
CREATE TABLE applications (
	id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, 						# Идентификатор
	user_id BIGINT UNSIGNED NOT NULL,												# Ссылка на продавца(Пользователя)
	product_name VARCHAR(100),														# Название товара
	description TEXT,																# Описание товара
	form_name VARCHAR(100),															# Форма товара(может переиспользоваться)
	weight BIGINT UNSIGNED NOT NULL,												# Вес товара в граммах
	img_address TEXT,																# id изображения в телеграм
	price DECIMAL(25, 2),															# Цена товара
	requested_at DATETIME DEFAULT NOW(),											# Дата подачи завки
	status ENUM (																	# Статус
		'На рассмотрении', 
		'Отколнена', 
		'Подтверждена') DEFAULT 'На рассмотрении', 
	UNIQUE(user_id, product_name, form_name, weight), 
	FOREIGN KEY(user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE
) COMMENT 'Заявки на добавление товарной позиции';

# Таблица способов доставки
DROP TABLE IF EXISTS delivery;
CREATE TABLE delivery (
	id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,							# Идентификатор
	delivery_name VARCHAR(100),														# Название курьерской службы
	commission_rate DECIMAL(25, 2)													# Комиссия руб.\км.
) COMMENT 'Способы доставки';

# Доступные способы доставки 
DROP TABLE IF EXISTS product_x_delivery;
CREATE TABLE product_x_delivery(
	product_id BIGINT UNSIGNED NOT NULL,											# Ссылка на товар
	delivery_id BIGINT UNSIGNED NOT NULL,											# Ссылка на службу доставки
	delivery_type ENUM (															# Тип доставки
		'Курьер',
		'Самовывоз'),
	PRIMARY KEY (product_id, delivery_id),
	FOREIGN KEY(product_id) REFERENCES products(id) ON UPDATE CASCADE ON DELETE CASCADE,
	FOREIGN KEY(delivery_id) REFERENCES delivery(id) ON UPDATE CASCADE ON DELETE CASCADE
) COMMENT 'Связь товаров и способов доставки';

# Представление пользовательской корзины
CREATE OR REPLACE VIEW basket AS (
	SELECT o.user_id, 												# Ссылка на пользователя
	d.product_name, 												# Название продукта
	f.form_name,													# Форма продукта
	p.weight,														# Вес продукта в граммах
	COUNT(*) cnt, 														# Кол-во в штуках
	sum(p.price) `sum`												# Сумма каждой группы
FROM orders o 
JOIN products p on o.product_id = p.id 
JOIN describes d on p.describe_id = d.id 
JOIN forms f on p.form_id = f.id
GROUP BY o.user_id, d.product_name, f.form_name, p.weight);

# Доступные способы доставки для каждого товара продовца
CREATE OR REPLACE VIEW delivery_info AS (
	SELECT
		u.fullname 'Продавец',
		d2.product_name 'Товар',
		d.delivery_name 'Доставка',
		pxd.delivery_type 'Способ'
	from product_x_delivery pxd 
	join products p on pxd.product_id = p.id 
	JOIN delivery d on pxd.delivery_id = d.id 
	JOIN describes d2 on p.describe_id = d2.id
	JOIN sellers_x_product sxp on pxd.product_id = sxp.product_id 
	join users u on sxp.user_id = u.id 
	order by u.fullname, d2.product_name, d.delivery_name, pxd.delivery_type
	);

# Процедура  добавляет подтвержденный товар в связанные таблицы 
DELIMITER //
CREATE PROCEDURE application_approve(IN application_id BIGINT) 
BEGIN
	START TRANSACTION;
	UPDATE applications SET status = 'Подтверждена' where id = application_id;
	INSERT INTO describes(product_name, img_address, description)
	SELECT product_name, img_address, description FROM applications WHERE id = application_id;
	SET @describe_id := LAST_INSERT_ID();
	INSERT INTO forms(form_name) SELECT form_name FROM applications WHERE id = application_id;
	SET @form_id := LAST_INSERT_ID();
	INSERT INTO products(describe_id, weight, form_id, price) 
	SELECT @describe_id, weight, @form_id, price from applications WHERE id = application_id;
	SET @product_id := LAST_INSERT_ID();
	INSERT INTO sellers_x_product(user_id, produt_id) 
	SELECT user_id, @product_id from applications WHERE id = application_id;
	COMMIT;
END//
DELIMITER ;

# Процедура удаляет позицию из корзины, указанную пользователем
DELIMITER //
CREATE PROCEDURE del_position(IN user_id, position_num BIGINT)
BEGIN
	START TRANSACTION;
	DELETE
	FROM orders  
	WHERE product_id in (
		SELECT product_id 
		FROM(
			SELECT ROW_NUMBER() OVER(ORDER BY o.product_id, f.form_name, p.weight ASC) AS num,
				o.product_id,
				sum(p.price)
			FROM orders o 
			JOIN products p on o.product_id = p.id 
			JOIN forms f on p.form_id = f.id
			WHERE o.user_id = user_id
			GROUP BY o.product_id, f.form_name, p.weight) t1
		WHERE num = position_num);
	COMMIT;
END
DELIMITER ;


# Триггер удаляет все товары продавца в случае удаления самого продовца 
DELIMITER //
CREATE TRIGGER After_Delete_sellers AFTER DELETE
ON sellers
FOR EACH ROW
BEGIN
    DELETE  
	FROM products p 
	WHERE id in (
	SELECT product_id
	FROM sellers_x_product sxp 
	WHERE user_id = OLD.user_id);
END //
DELIMITER ;

# Триггер удаляет решенные/отклоненные вопросы пользователей
DELIMITER //
CREATE TRIGGER After_Delete_products AFTER DELETE  
ON questions
FOR EACH ROW
BEGIN
	DELETE
	FROM questions 
	WHERE id in(
	select min(id)
	FROM questions
	WHERE status = 'Решен'
	or status = 'Отклонен');
END //
DELIMITER ;