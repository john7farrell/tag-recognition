drop table if exists entries;
create table 'entries' (
	id integer primary key autoincrement,
	title text not null,
	'ProductId' text not null,
	'Origin' text not null,
	'Part' text not null,
	'Material' text not null,
	'Percent' text not null,
	'Filename' text not null UNIQUE ON CONFLICT REPLACE,
	'FullText' text not null
);
