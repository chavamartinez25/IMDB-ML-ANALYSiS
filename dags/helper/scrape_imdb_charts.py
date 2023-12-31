# web_scraping helper

import requests
from bs4 import BeautifulSoup
import os
import sys
from google.cloud import bigquery
import datetime
import pandas as pd

# Creating an Environmental Variable for the service key confguration
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/opt/airflow/dags/configs/ServiceKey_GoogleCloud.json'

# Create a client
bigquery_client = bigquery.Client()

def _get_soup(chart):
    '''
        Get the BeautifulSoup object from url.
        Args:
            - chart(str) = chart to scrape
                Options: 'most_popular_movies', 'top_250_movies', 'top_english_movies', 'top_250_tv'
        Returns:
            - soup(BeautifulSoup) = BeautifulSoup object
    '''

    # Send a get request an parse using BeautifulSoup
    if chart == 'most_popular_movies':
        url = 'https://www.imdb.com/chart/moviemeter?pf_rd_m=A2FGELUUNOQJNL&pf_rd_p=470df400-70d9-4f35-bb05-8646a1195842&pf_rd_r=5V6VAGPEK222QB9E0SZ8&pf_rd_s=right-4&pf_rd_t=15506&pf_rd_i=toptv&ref_=chttvtp_ql_2'

    if chart == 'top_250_movies':
        url = 'https://www.imdb.com/chart/top/?pf_rd_m=A2FGELUUNOQJNL&pf_rd_p=470df400-70d9-4f35-bb05-8646a1195842&pf_rd_r=5V6VAGPEK222QB9E0SZ8&pf_rd_s=right-4&pf_rd_t=15506&pf_rd_i=toptv&ref_=chttvtp_ql_3'

    if chart == 'top_english_movies':
        url = 'https://www.imdb.com/chart/top-english-movies?pf_rd_m=A2FGELUUNOQJNL&pf_rd_p=470df400-70d9-4f35-bb05-8646a1195842&pf_rd_r=3YMHR1ECWH2NNG5TPH1C&pf_rd_s=right-4&pf_rd_t=15506&pf_rd_i=boxoffice&ref_=chtbo_ql_4'

    if chart == 'top_250_tv':
        url = 'https://www.imdb.com/chart/tvmeter?pf_rd_m=A2FGELUUNOQJNL&pf_rd_p=470df400-70d9-4f35-bb05-8646a1195842&pf_rd_r=J9H259QR55SJJ93K51B2&pf_rd_s=right-4&pf_rd_t=15506&pf_rd_i=topenglish&ref_=chttentp_ql_5'


    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    response = requests.get(url, headers = headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def _scrape_movies (soup):
    '''
        Scrape the most popular titles ans ratings from the IMDB website.
        Args:
            - soup(BeautifulSoup) = BeautifulSoup object
        Returns: 
            - movie_dict(dict) = Dictionary of movie names and ratings
    '''

    # Find all movie names in the URL
    movie_names = []
    movie_years = []
    movie_ratings = []
    user_voting = []

    # Find all movie in the URL
    titlesRefs = soup.find_all('div',{'class':'cli-children'})

    # Collect movie title, release year, ratings and user voting
    for title in titlesRefs:
        
        # TITULO
        try:
            titleMovie = title.find_all('h3',{'class':'ipc-title__text'})
            movie_names.append(titleMovie[0].get_text())
        except:
            print('Missing title. Replacing with -1')
            movie_names.append(-1)
        
        # AÑO
        try:
            yearMovie = title.find_all('span',{'class':'cli-title-metadata-item'})
            movie_years.append(int(yearMovie[0].get_text()))
        except: 
            print('Missing year. Replacing with -1')
            movie_years.append(-1)
        
        # RATING
        try:
            ratingMovie = title.find_all('span',{'class':'ipc-rating-star'})
            movie_ratings.append(float(ratingMovie[0].get_text()[0:3]))
        except: 
            print('Missing rating. Replacing with -1')
            movie_ratings.append(-1)
        
        # VOTES
        try:
            movieVote = title.find_all('span',{'class':'ipc-rating-star'})
            n = movieVote[0].get_text()[3:len(movieVote[0].get_text())]
            n = n.replace('(','')
            n = n.replace(')','')
            if 'K' in n:
                f = int(n.replace('K','')) * 1000
            elif 'M' in n:
                f = int(float(n.replace('M','')) * 1000000)
            user_voting.append(f)
        except: 
            print('Missing votes. Replacing with -1')
            user_voting.append(-1)
    
    # Create a dataframe
    movie_df = pd.DataFrame({'movie_name': movie_names, 'movie_year': movie_years, 'movie_rating': movie_ratings, 'movie_votings': user_voting})

    # Add movie_id
    movie_df['movie_id'] = movie_df.index + 1

    # set date
    movie_df['update_date'] = datetime.datetime.today().strftime('%Y-%m-%d')

    # Reorder columns
    movie_df = movie_df[['movie_id', 'movie_name','movie_year','movie_rating','movie_votings','update_date']]

    return movie_df


def _getOrCreate_dataset(dataset_name : str) -> bigquery.dataset.Dataset:
    '''
    Get dataset. If the dataset does not exist, create it.

    Args:
        - dataset_name(str) = Name of the new/existing data set.
        - project_id(str) = project id(default = The project id of the bigquery_client object)
    
    Return:
        - dataset(google.cloud.bigquery.datasetr.Dataset) = Google BigQuery Dataset
    '''

    print('Fetching Dataset...')
    
    try:
        # Get and return dataset if exist
        dataset = bigquery_client.get_dataset(dataset_name)
        print('Done data set from try')
        print(dataset.self_link)
        return dataset
    
    except Exception as e:
        # If not, reate and return dataset
        if e.code == 404:
            print('Data set does not exist. Creating a new one.')
            bigquery_client.create_dataset(dataset_name)
            dataset = bigquery_client.get_dataset(dataset_name)
            print('Done data set from exept')
            print(dataset.self_link)
            return dataset
        else:
            print(e)

def _getOrCreate_table(dataset_name:str, table_name:str) -> bigquery.table.Table:
    '''
        Create a table. If the table already exist, return it.

        Args:
            - table_name(str) = Name of new/existing table.
            - dataset_name(str) = Name of the new/existing data set.
            - project_id(str) = project id(default = The project id of the bigquery_client object)

        Returns:
            - table(google.cloud.bigquery.table.Table) = Google BigQuery table
    '''
    dataset = _getOrCreate_dataset(dataset_name)
    project = dataset.project
    dataset = dataset.dataset_id
    table_id = project + '.' + dataset + '.' + table_name

    print('\nFetching Table...')

    try:
        # Get table if exist
        table = bigquery_client.get_table(table_id)
        print('Done create table from try')
        print(table.self_link)
    
    except Exception as e:
        # If not, create and get table
        if e.code == 404:
            print('Table does not exist. Creating a new one')
            bigquery_client.create_table(table_id)
            table = bigquery_client.get_table(table_id)
            print(table.self_link)
        else:
            print(e)
    
    finally:
        return table


def _load_to_bigQuery(movie_names, chart, dataset_name = 'imdb'):
    '''
        Load data into BigQuery table.
        Args:
            - movie_names(pd.DataFrame) = dataframe of movies names
            - chart(str) = Name of the chart
                Options: most_popular_movies, top_250_movies, top_english_movies, top_250_tv
            - dataset_name(str) = Name of the new/existing data set
            - date_to_load(datetime.datetime) = Date to load into the table
        Returns:
            - None
        Notes:
            - The function will create a new dataset and table if they do not exist
            - The function will overwrite the table if it already exist    
    '''

    if chart == 'most_popular_movies':
        table_name = 'most_popular_movies'
    
    if chart == 'top_250_movies':
        table_name = 'top_250_movies'
    
    if chart == 'top_english_movies':
        table_name = 'top_english_movies'
    
    if chart == 'top_250_tv':
        table_name = 'top_250_tv'

    # Create a table
    table = _getOrCreate_table(dataset_name, table_name)

    # Create a job config
    job_config = bigquery.LoadJobConfig(
        source_format = bigquery.SourceFormat.CSV,
        schema = [
            bigquery.SchemaField("movie_id",bigquery.enums.SqlTypeNames.INT64),
            bigquery.SchemaField("movie_name",bigquery.enums.SqlTypeNames.STRING),
            bigquery.SchemaField("movie_year",bigquery.enums.SqlTypeNames.INT64),
            bigquery.SchemaField("movie_rating",bigquery.enums.SqlTypeNames.FLOAT64),
            bigquery.SchemaField("movie_votings",bigquery.enums.SqlTypeNames.INT64),
            bigquery.SchemaField("update_date",bigquery.enums.SqlTypeNames.DATE),
        ],
        write_disposition = "WRITE_TRUNCATE",
    )

    # Load data into the table
    job = bigquery_client.load_table_from_dataframe(
        movie_names, table, job_config = job_config
    )

    # Wait for the job to complete
    job.result()

    # Check if the job is done
    print("Loaded {} rows into {}:{}".format(job.output_rows, dataset_name, table_name))



# Main function
""" def main():
    soup = _get_soup(chart='top_250_movies')
    movies_df = _scrape_movies(soup)
    _load_to_bigQuery(movies_df, chart='top_250_movies')
    print(movies_df)

if __name__ == '__main__':
    main() """
