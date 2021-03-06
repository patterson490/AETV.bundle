TITLE = 'A&E'
SHOWS_URL = 'http://www.aetv.com/shows'
BASE_PATH = 'http://www.aetv.com'

####################################################################################################
def Start():

	ObjectContainer.title1 = TITLE
	HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
@handler('/video/aetv', TITLE)
def MainMenu():

	oc = ObjectContainer()

	oc.add(DirectoryObject(key=Callback(PopShows, title="Most Popular"), title="Most Popular"))
	oc.add(DirectoryObject(key=Callback(MainShows, title="Featured"), title="Featured"))
	oc.add(DirectoryObject(key=Callback(MainShows, title="Classics"), title="Classics"))

	return oc

#####################################################################################################
@route('/video/aetv/mainshows')
def MainShows(title):

	oc = ObjectContainer(title2=title)

	data = HTML.ElementFromURL(SHOWS_URL)
	# this gets shows from each section of the menu on the show page for featured and classics
	showList = data.xpath('//div/strong[text()="%s	"]/parent::div/following-sibling::div//ul/li/a' %title)

	for s in showList:
		url = s.xpath('./@href')[0]

		if not url.startswith('http://'):
			url = BASE_PATH + url

		show = s.xpath('text()')[0]

		oc.add(DirectoryObject(key = Callback(ShowSection, url=url, title=show), title = show))

	return oc

###################################################################################################
# This function gets the shows that have images for popular shows
@route('/video/aetv/popshows')
def PopShows(title):

	oc = ObjectContainer(title2=title)

	data = HTML.ElementFromURL(SHOWS_URL)
	showList = data.xpath('//div/h2[text()="Most Popular"]/parent::div//li/div/a')

	for s in showList:
		thumb = s.xpath('./img/@src')[0]
		url = s.xpath('./@href')[0]

		if not url.startswith('http://'):
			url= BASE_PATH + url

		show = s.xpath('./img/@alt')[0]

		oc.add(DirectoryObject(key = Callback(ShowSection, url=url, title=show, thumb = thumb), thumb = thumb, title = show))

	return oc

####################################################################################################
@route('/video/aetv/showsection')
def ShowSection(title, url, thumb=''):

	oc = ObjectContainer(title2=title)

	if thumb:
		oc.add(DirectoryObject(key=Callback(ShowsPage, title="Full Episodes", url=url, vid_type='full-episode'), title="Full Episodes", thumb=thumb))
		oc.add(DirectoryObject(key=Callback(ShowsPage, title="Clips", url=url, vid_type='clips'), title="Clips", thumb=thumb))
	else:
		oc.add(DirectoryObject(key=Callback(ShowsPage, title="Full Episodes", url=url, vid_type='full-episode'), title="Full Episodes"))
		oc.add(DirectoryObject(key=Callback(ShowsPage, title="Clips", url=url, vid_type='clips'), title="Clips"))

	return oc

####################################################################################################
@route('/video/aetv/showspage')
def ShowsPage(url, title, vid_type):

	oc = ObjectContainer(title2=title)

	if url.endswith('/video'):
		local_url = url
	else:
		local_url = url +'/video'

	data = HTML.ElementFromURL(local_url)		
	allData = data.xpath('//ul[@id="%s-ul"]/li[not(contains(@class, "behind-wall"))]' %vid_type)

	for s in allData:
		class_info = s.xpath('./@class')[0]

		# Ads are picked up in this list so we check for an ending of -ad
		if class_info.endswith('-ad'):
			continue

		title = s.xpath('./@data-title')[0]
		thumb_url = s.xpath('./a/img/@src')[0]

		video_url = s.xpath('./a/@href')[0]
		if not video_url.startswith('http:'):
			video_url = BASE_PATH + video_url

		duration = Datetime.MillisecondsFromString(s.xpath('.//span[contains(@class,"duration")]/text()')[0])
		summary = s.xpath("./@data-description")[0]

		try: episode = int(s.xpath('.//span[contains(@class,"tile-episode")]/text()')[0].split('E')[1])
		except: episode = None

		if episode:
			try: season = int(s.xpath('.//span[contains(@class,"season")]/text()')[0].split('S')[1])
			except: season = 1

			date = s.xpath('./@data-date')[0]

			if ': ' in date:
				date = Datetime.ParseDate(date.split(': ')[-1])
			else:
				date = None

			oc.add(
				EpisodeObject(
					url = video_url,
					title = title,
					duration = duration,
					summary = summary,
					thumb = Resource.ContentsOfURLWithFallback(url=thumb_url),
					originally_available_at = date,
					index = episode,
					season = season
				)
			)
		else:
			oc.add(
				VideoClipObject(
					url = video_url,
					title = title,
					duration = duration,
					summary = summary,
					thumb = Resource.ContentsOfURLWithFallback(url=thumb_url)
				)
			)

	if len(oc) < 1:
		#Log ('still no value for objects')
		return ObjectContainer(header="Empty", message="There are no videos to display for this show right now.") 
	else:
		return oc
