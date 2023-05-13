CREATE TABLE categories(id integer primary key, name text);
CREATE TABLE items(id integer primary key, name text, category_id integer, image_name text, foreign key (category_id) references categories(id));
