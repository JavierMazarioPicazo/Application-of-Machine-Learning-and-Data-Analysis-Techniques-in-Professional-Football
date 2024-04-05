# Application of Machine Learning and Data Analysis Techniques in Professional Football

This repository presents the master's thesis of Javier Mazarío Picazo. It has two main developments: 

* Clustering of teams and players.
* Web applicaction with match reports.


## Clustering of teams and players

There are two main files for this development PlayerPerformance.ipynb and TeamPerformance.ipynb. The fundamental development here is the collection of data by connecting to the Statsbomb API, the processing of the data to obtain aggregate metrics and statistics by players and teams, and the application of the unsupervised machine learning algorithm K-Means with the objective of clustering teams and players with similar performance, allowing their comparison and the drawing of conclusions. 

## Web Application

The web application is developed with the Streamlit library. In order to make use of this application, the DataProcessing.ipynb notebook must first be executed in order to obtain the data with which the application works. The application is developed as a tool to support the work done by analysts within a technical staff. It shows match reports with different visualizations that allow the detailed analysis of player actions during the course of the match.

* Result.
* Lineups.
* Passmap.
* Heatmap.
* Shotmap.
* Passing network.


