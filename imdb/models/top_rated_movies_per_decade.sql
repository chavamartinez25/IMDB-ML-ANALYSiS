/*Top rated movies per decade*/
SELECT *
FROM
(
  SELECT
    movie_year,
    movie_name,
    decade,
    movie_rating,
    row_number() OVER (PARTITION BY decade ORDER BY movie_rating DESC) AS rank
  FROM
  (
    SELECT 
      m1.movie_year,
      m1.movie_name,
      m1.movie_rating,
      CASE
        WHEN m1.movie_year BETWEEN 1920 AND 1930 THEN '20s'
        WHEN m1.movie_year BETWEEN 1930 AND 1940 THEN '30s'
        WHEN m1.movie_year BETWEEN 1940 AND 1950 THEN '40s'
        WHEN m1.movie_year BETWEEN 1950 AND 1960 THEN '50s'
        WHEN m1.movie_year BETWEEN 1960 AND 1970 THEN '60s'
        WHEN m1.movie_year BETWEEN 1970 AND 1980 THEN '70s'
        WHEN m1.movie_year BETWEEN 1980 AND 1990 THEN '80s'
        WHEN m1.movie_year BETWEEN 1990 AND 2000 THEN '90s'
        WHEN m1.movie_year BETWEEN 2000 AND 2010 THEN '2000s'
        WHEN m1.movie_year BETWEEN 2010 AND 2020 THEN '2010s'
        WHEN m1.movie_year BETWEEN 2020 AND 2030 THEN '2020s'
      END AS decade
    FROM imdb.top_250_movies AS m1
    FULL JOIN imdb.most_popular_movies AS m2 ON ( m1.movie_name = m2.movie_name )
    FULL JOIN imdb.top_english_movies AS m3 ON ( m1.movie_name = m3.movie_name )
    ORDER BY m1.movie_year DESC
  ) AS aaa
  WHERE
    aaa.movie_name IS NOT NULL
) bbb
WHERE
  bbb.rank = 1
ORDER BY
  bbb.movie_year DESC