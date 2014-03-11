#!/usr/bin/env python
import sys
import math
from BeautifulSoup import BeautifulStoneSoup, Tag, NavigableString

def POWER(speed_mps):
    # http://www.kurtkinetic.com/powercurve.php
    # kinecit_power_curve = P = (5.244820) * S + (0.019168) * S^3
    speed = speed_mps * 2.23694
    power = 5.24482 * speed + 0.019168 * math.pow(speed, 3)
    return power

def writeFile(soup, new_name):
    contents = soup.prettify()
    with open(new_name, "wb") as file:
        file.write(contents)

def loadFile(filename):
    soup = BeautifulStoneSoup(open(filename).read())
    return soup

def modFile(soup):
    sum_pwr_min = 9999
    sum_pwr_max = -9999
    sum_pwr_avg = 0
    count = 0
    pwr_min = 0
    pwr_max = 0
    pwr_avg = 0
    average_window = []
    averages = []

    #samples
    for seg in soup.contents[2].findAll("sample"):
        spd = float(seg.find("spd").string)
        tp = Tag(soup, "pwr")
        tn = NavigableString(u"\n")
        seg.insert(7, tp)
        seg.insert(8, tn)
        pwr = POWER(spd)
        tp.setString(unicode(pwr))
        #print "spd: %s => pwr: %s" % (spd * 2.23694, pwr)

        # This implicitly assumes samples are every 1 sec for 30 sec average
        average_window.append(pwr)
        if ( len(average_window) >= 30 ):
            pwr_ave = sum(average_window[-30:]) / 30
            averages.append(pwr_ave)
            average_window = average_window[-29:]

    #segments
    for seg in soup.contents[2].findAll("segment"):
        count += 1

        s = float(seg.find("spd")['min'])
        pwr_min = POWER(s)
        if (pwr_min < sum_pwr_min): sum_pwr_min = pwr_min

        s = float(seg.find("spd")['max'])
        pwr_max = POWER(s)
        if (pwr_max > sum_pwr_max): sum_pwr_max = pwr_max

        s = float(seg.find("spd")['avg'])
        pwr_avg = POWER(s)
        sum_pwr_avg = sum_pwr_avg + pwr_avg

        seg.find("pwr")['min'] = unicode(pwr_min)
        seg.find("pwr")['max'] = unicode(pwr_max)
        seg.find("pwr")['avg'] = unicode(pwr_avg)

        #print "%s => Min: %s Max: %s Avg: %s" % (s*2.23694, pwr_min, pwr_max, pwr_avg)

    #summarydata
    sum_pwr_avg = sum_pwr_avg / count
    soup.contents[2].find("summarydata").find("pwr")['min'] = unicode(sum_pwr_min)
    soup.contents[2].find("summarydata").find("pwr")['max'] = unicode(sum_pwr_max)
    soup.contents[2].find("summarydata").find("pwr")['avg'] = unicode(sum_pwr_avg)

    #print "S Min: %s Max: %s Avg: %s", (sum_pwr_min, sum_pwr_max, sum_pwr_avg)

    quad_averages = map(lambda x: math.pow(x, 4), averages)
    ave_quad = sum(quad_averages) / len(quad_averages)
    norm_pwr = math.pow(ave_quad, 1/4.0)
    soup.contents[2].find("summarydata").normalizedpower = norm_pwr
    #print "ave pwr: %s" % (norm_pwr)

#    1) starting at the 30 s mark, calculate a rolling 30 s average (of the preceeding time points, obviously).
#    2) raise all the values obtained in step #1 to the 4th power.
#    3) take the average of all of the values obtained in step #2.
#    4) take the 4th root of the value obtained in step #3.
#    http://home.trainingpeaks.com/blog/article/normalized-power,-intensity-factor-training-stress
#    http://cyclingtips.com.au/2009/07/average-vs-normalized-power/
#    http://www.endurancecorner.com/wko_definitions

# AveragePower: http://www.slowtwitch.com/Training/General_Physiology/Measuring_Power_and_Using_the_Data_302.html

    """
<sample>
<timeoffset>3852</timeoffset>
<hr>133</hr>
<spd>4.906667</spd>
<cad>79</cad>
<dist>23015.523438</dist>
</sample>
"""
    return

if __name__ == "__main__":
    file_name = sys.argv[1]
    soup = loadFile(file_name)

    modFile(soup)

    new_name = file_name.rsplit(".")
    new_name[0] = new_name[0] + "-mod."
    new_name = "".join(new_name)
    writeFile(soup, new_name)
