/* Top reted movies por year */

SELECT
    movie_year,
    movie_name,
    movie_rating
FROM
    (
        SELECT
            m1.movie_year,
            m1.movie_name,
            m1.movie_rating,
            row_number() OVER (PARTITION BY m1.movie_year ORDER BY m1.movie_rating DESC) AS rank
        FROM imdb.top_250_movies AS m1
            FULL JOIN  imdb.most_popular_movies AS m2 ON (m1.movie_name = m2.movie_name)
            FULL JOIN  imdb.top_english_movies AS m3 ON (m1.movie_name = m3.movie_name)
        ORDER BY m1.movie_year DESC
    ) AS aaa
WHERE 
    aaa.rank = 1