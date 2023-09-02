/*User voting trend*/

SELECT 
  movie_year,
  total_votes,
  ROUND((total_votes + (LAG(total_votes, 2) over(ORDER BY movie_year)) + (LAG(total_votes, 1) OVER(ORDER BY movie_year ))) / 3, 2) AS Moving_Average_3
FROM
(
    SELECT 
      m1.movie_year,
    SUM(m1.movie_votings) AS total_votes
    FROM imdb.top_250_movies AS m1
    LEFT JOIN imdb.most_popular_movies AS m2 ON ( m1.movie_name = m2.movie_name )
    LEFT JOIN imdb.top_english_movies AS m3 ON ( m1.movie_name = m3.movie_name )
    GROUP BY
      m1.movie_year
) AS aaa
ORDER BY movie_year