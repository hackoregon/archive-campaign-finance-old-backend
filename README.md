Hack Oregon
=======
Welcome to Hack Oregon's official github repository.  Hack Oregon is a new kind of civic action group emerging to tackle tough questions arising between the current political establishment and the evolving landscape.  We strive to use data as a medium to spark engagement in Oregon's political process.


# Our Technical Goals
* Scrape raw data from https://secure.sos.state.or.us/orestar/CommitteeSearchFirstPage.do?startup=2 and make it easier to consume
* Visualize results


To run the demo locally you will need the following data file:

https://s3-us-west-2.amazonaws.com/mp-orestar-dump/all.pickle

Then just run 'python demo.py' and the server will run locally on port 5000.

The data is also available in CSVs. https://s3-us-west-2.amazonaws.com/mp-orestar-dump/orestar.tgz


The postgres database dump:

https://s3-us-west-2.amazonaws.com/mp-orestar-dump/hackoregon.sql.gz


Some example queries:

select filer_id, sum(amount) from raw_committee_transactions group by filer_id order by sum(amount) desc limit 10;


---------------------------------------------

select d.date, count(rt.tran_id), sum(rt.amount) from (select to_char(date_trunc('day', (current_date - offs)), 'YYYY-MM-DD') as date from generate_series(0, 365, 1) as offs) d left outer join raw_committee_transactions rt on (d.date=to_char(date_trunc('day', rt.tran_date), 'YYYY-MM-DD') and rt.sub_type = 'Cash Expenditure' and filer_id = 1524) group by d.date;

---------------------------------------------

select sub_type, sum(amount) from raw_committee_transactions group by sub_type order by sum(amount) desc;

---------------------------------------------


select filer, purp_desc, amount from raw_committee_transactions where purp_desc_vectors @@ to_tsquery('golf') order by amount desc limit 5;


---------------------------------------------


select tran_date, filer_id, sum(amount), count(amount) from raw_committee_transactions where filer_id in (select filer_id from raw_committee_transactions group by filer_id order by sum(amount) desc limit 10) and sub_type = 'Cash Expenditure' group by tran_date, filer_id order by tran_date desc, sum desc;

---------------------------------------------


WITH dates_table AS (
    SELECT tran_date::date AS date_column, filer_id, sub_type, SUM(amount) OVER (PARTITION BY filer_id ORDER BY amount desc) FROM raw_committee_transactions WHERE
     filer_id in (SELECT filer_id FROM raw_committee_transactions GROUP BY filer_id ORDER BY SUM(amount) DESC LIMIT 10)
)
SELECT series_table.date, dates_table.filer_id, dates_table.sub_type, dates_table.sum, COUNT(dates_table.date_column), SUM(COUNT(dates_table.date_column)) OVER (ORDER BY series_table.date) FROM (
    SELECT (last_date - b.offs) AS date
        FROM (
            SELECT GENERATE_SERIES(0, last_date - first_date, 1) AS offs, last_date from (
                 SELECT MAX(date_column) AS last_date, (MAX(date_column) - '1 year'::interval)::date AS first_date FROM dates_table
            ) AS a
        ) AS b
) AS series_table
LEFT OUTER JOIN dates_table
    ON (series_table.date = dates_table.date_column)
GROUP BY series_table.date, dates_table.filer_id, dates_table.sub_type, dates_table.sum
ORDER BY series_table.date;



AWS login
---------

https://308682604918.signin.aws.amazon.com/console
