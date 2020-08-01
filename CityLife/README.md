
# CityLife

CityLife is an investigation into the characteristics of ghost towns in America. The basic finding is that Wikipedia articles describing ghost towns disproportionately use terminology implying boom towns. That is, based on the terminology, most ghost towns were once towns which formed around a natural resource such as gold or oil, and then dwindled and died out as the resource ran out, was extracted up to diminishing returns, or lost value due to general market dynamics.

Arguably all cities are geographic. The uniqueness of ghost towns is that their geographic characteristic was isolated and temporary. This is in contrast to cities whose geographic characteristics are more resilient, such as nearby bodies of water that can serve as commercial transport channels.

### Usage example

\# First, get a list of cities through the counties Wikipedia article.  
`python Wikipedia_Counties.py --directory my_directory`

\# Then, get lists of cities from individual state Wikipedia articles.  
`python Wikipedia_States.py --directory my_directory`

This will generate files which can be used to download the appropriate articles in bulk from https://en.wikipedia.org/wiki/Special:Export.