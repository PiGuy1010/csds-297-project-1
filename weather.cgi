#! /bin/bash
echo "Content-type: text/html"; echo
echo "<h1>Get the current and forecasted temperatures for any location in the United States from multiple sources.</h1>"
echo "<li>National Weather Service"
echo "<li>The Weather Channel"
echo "<li>Weather Underground"
echo "<hr>"
# If there is no input already, then ask for either a zip code or a city and state.
if [[ -z $QUERY_STRING ]]; then
	echo "<form action='weather.cgi' method='GET'>"
	echo "  <textarea cols=80 rows=1 name='zipcode'>"
	echo "Enter a zip code"
	echo "</textarea>"
	echo "  <input type=submit>"
	echo "</form>"
	echo "<form action='weather.cgi' method='GET'>"
	echo "  <textarea cols=80 rows=1 name='location'>"
	echo "Enter a city, state"
	echo "</textarea>"
	echo "  <input type=submit>"
	echo "</form>"
elif [[ -n $QUERY_STRING ]]; then	
	regex=" *class=\"CurrentConditions\-\-tempValue\-\-3KcTQ\">"
	regex2="<*type=\"temperature\" _nghost\-sc144=\"\"><span _ngcontent\-sc144=\"\" class=\"test\-true wu\-unit wu\-unit\-temperature is\-degree\-visible ng\-star\-inserted\"><\!\-\-\-\-><\!\-\-\-\-><\!\-\-\-\-><span _ngcontent\-sc144=\"\" class=\"wu\-value wu\-value\-to\" style=\"color:;\">"
	regex3="<p class=\"myforecast\-current\-lrg\">"
	if [[ ${QUERY_STRING::8} == "zipcode=" ]]; then
		# It's possible to easily get weather data using only a zip code through weather.com, so we search that website first and then get other location data to use for the other websites.
		rmpref=${QUERY_STRING#"zipcode="}
		justzip=${rmpref//%0D%0A/}
		echo "You entered the zip code $justzip"
		echo "<hr>"
		wget -q -O /dev/stdout "weather.com/weather/today/l/${justzip}" > /tmp/temp.html # Use wget to get weather.com's page for this zip code and put it into /tmp/temp.html
		if ! [[ -s "/tmp/temp.html" ]]; then # Condition for if /tmp/temp.html is empty (the wget failed because the zip code wasn't valid)
			echo "Couldn't find information for this zip code."
		fi
		while IFS= read myline; do
			if [[ $myline =~ $regex ]]; then
				cutpref=${myline#$regex} # Removing everything up to the current temperature in myline
				temperature=${cutpref%%°*} # Removing everything from the degree symbol and beyond, so that only the Fahrenheit temperature is left
				echo "The Weather Channel: $temperature"
				echo -e "\xb0 F" # \xb0 encodes the degree symbol
				echo "<hr>"
			fi
			locregex=" *Today’s and tonight’s "
			if [[ $myline =~ $locregex ]]; then # Determining the location from the initial wget of weather.com (to be used later)
				cutpref=${myline##$locregex}
				location=${cutpref%% weather*}
			fi
			latregex=" *latitude\\\":"
			longregex=" *longitude\\\":"
			if [[ $myline =~ $latregex ]]; then # Determining the latitude and longitude
				cutpref=${myline#$latregex}
				lat=${cutpref%%,*}
				cutmore=${myline#$longregex}
				long=${cutmore%%,*}
			fi
		done < /tmp/temp.html
		# Other sites
		state=${location:(-2)}
		city=${location:0:$((${#location}-4))}
		wget -q -O /dev/stdout "wunderground.com/weather/us/$state/$city" > /tmp/temp.html
		while IFS= read myline; do
			if [[ $myline =~ $regex2 ]]; then
				cutpref=${myline#$regex2}
				temp2=${cutpref%%<*}
				echo "Weather Underground: $temp2"
				echo -e "\xb0 F"
				echo "<hr>"
			fi
		done < /tmp/temp.html
		wget -q -O /dev/stdout "forecast.weather.gov/MapClick.php?lat=$lat&lon=$long" > /tmp/temp.html
		while IFS= read myline; do
			if [[ $myline =~ $regex3 ]]; then
				cutpref=${myline##*\">}
				temp3=${cutpref%%\&*}
				echo $"National Weather Service: $temp3"
				echo -e "\xb0 F"
				echo "<hr>"
			fi
		done < /tmp/temp.html
	elif [[ ${QUERY_STRING::9} == "location=" ]]; then
		rmpref=${QUERY_STRING#"location="}
		justloc=${rmpref//%0D%0A/}
		echo "You entered the location $justloc"
		echo "<hr>"
		# It's easiest to get Weather Underground's data from just a location, so that is what we do first in this case.
		state=${justloc:(-2)}
		city=${location:0:$((${#location}-4))}
		wget -q -O /dev/stdout "wunderground.com/weather/us/$state/$city" > /tmp/temp.html
		latregex=" *lat="
		longregex=" *lon="
		while IFS= read myline; do
			if [[ $myline =~ $regex2 ]]; then
				echo ""
			fi
			if [[ $myline =~ $latregex ]]; then
				cutpref=${myline#$latregex}
				lat=${cutpref%%&*}
				cutmore=${myline#$longregex}
				long=${cutmore%%&*}
			fi
		done < /tmp/temp.html
		wget -q -O /dev/stdout "forecast.weather.gov/MapClick.php?lat=$lat&lon=$long" > /tmp/temp.html
	fi
fi
