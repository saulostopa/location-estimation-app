## Tower Jumps

A mobile carrier (e.g., AT&T, Verizon, T-Mobile) tracks a subscriber’s location using a method
called cell tower triangulation, a method for determining the location of a phone by measuring
the time it takes for a signal to travel between the phone and multiple cell towers. Cell tower
triangulation, unlike GPS, is not very precise. Consider a subscriber who lives very close to a
state or country border. The subscriber uses a mobile application that needs to accurately
record the state or country that the subscriber is physically located in. The application does not
use GPS to minimize battery consumption on the device, but instead only has access to
locations based on cell tower triangulation. In such a scenario, the application may receive
location data from cellphone towers located in more than one state or country making it appear
that the subscriber was in two places at the same time.

You are developing an application that estimates which state (or country) a subscriber may be in
during different time intervals during the day, and an indicator that expresses the confidence in
the estimated location.

To help with the assignment, attached is a data file that provides location data for a single
subscriber, John Doe. John Doe has a home very close to the border of NY and CT and so
experiences a ping-pong of locations recorded across state borders. As an example refer to Jan
5-10, 2021 data in the attached data file. Clearly the subscriber cannot be going back and forth
between NY and CT so often. But what should the application tell the subscriber? Where are
they?

Carriers determine location of a subscriber based on a number of factors including distance
from the cell-phone tower, strength of the signal, humidity, temperature, proximity to a water
body etc. The data set provided is only one example. The same subscriber could be in the same
actual physical location, but could have had a different set of cell tower readings. Your solution
should contemplate these different scenarios.

‘Page Number’ and ‘Item Number’ refer to the page and the line item from the data report.
‘Record Type’ refers to whether the data is captured by the carrier as a result of a connection
that the mobile device made with the carrier for making/receiving a phone call, data or SMS.
The focus of this assignment is to understand how you think. It is ok to ask questions; feel free
to send a WhatsApp to +1 949.468.7885 so I can get back to you quickly.

## Feature
 - Determine Location and Confidence Level

## Scenario
- Provide a list of time periods and the state the person was in, as well as a confidence level

## Challenge

#### Given a set of data points with longitude, latitude, timestamp, and current state when the data points are processed:

- A report should be provided with a list of time periods
- The state where the person likely was during that interval
- The confidence level expressed as a percentage