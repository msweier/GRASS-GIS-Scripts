#!/usr/bin/env python
#
############################################################################
#
# MODULE:      r.qpe_rfc
# AUTHOR(S):   mweier 2016-02-19
#
#              
# PURPOSE:     Generate subbasin hyetograph file for DSS import from NWS River   Forecast Center radar adjusted rainfall
# COPYRIGHT:   
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#                
#
#############################################################################
 
#%Module
#% description: This script extracts recent QPE grids from the NWS River Forcast center and retains them in .tiff format, averaging values over subbasins, outputs text file of averages for import in to HEC-DSS
#% keywords: rainfall, radar, qpe, rfc
#%End
#%Option
#% key: basinrast
#% type: string
#% required: yes
#% multiple: no
#% key_desc: name
#% description: Categorical subbasin raster
#% answer: 
#% gisprompt: old,cell,raster
#%End
#%Option
#% key: rfc
#% type: string
#% required: yes
#% multiple: no
#% key_desc: name
#% description: River forecast center MB = missouri river basin NC = red
#% options: MB,NC
#%End
#%Option
#% key: res
#% type: string
#% required: no
#% multiple: no
#% key_desc: name
#% description: Region resolution
#% answer: 50
#%End
#%Option
#% key: start_date
#% type: string
#% required: yes
#% multiple: no
#% key_desc: name
#% description: Start date #yyyy_mm_dd# format, Begins in 1994
#% answer:
#%End
#%Option
#% key: end_date
#% type: string
#% required: yes
#% multiple: no
#% key_desc: name
#% description: End date #yyyy_mm_dd# format, Recent dates may not be available
#% answer:
#%End



from os.path import expanduser
import os, sys, glob, datetime
from datetime import date, timedelta
import time
import pprint as pp


import subprocess
import shutil


##==============================================================================
## #######For grass envrironment  debugging
##==============================================================================
#print "startGRASS_"
#
#os.environ['GIS_LOCK'] = str(os.getpid())
#envHome =  os.environ['HOME'] 
#os.environ['GISBASE'] = "/Applications/GRASS-6.4.app/Contents/MacOS"
#
## stuff that should be in PATH
#pathList = [os.path.join(os.environ['GISBASE'],'bin'), os.path.join(os.environ['GISBASE'],'scripts'), os.path.join(envHome,'Library','GRASS','6.4','Modules','bin'), os.path.join(envHome,'Library','GRASS','6.4','Modules','scripts'), os.path.join('/Library','Frameworks','GDAL.framework', 'Programs')]
#
## update PATH if needed
#for p in pathList:
#    if p not in os.environ['PATH']:
#        os.environ['PATH'] = os.environ['PATH'] + ':' + p
#        print 'adding ' + p + ' to PATH'
#        
##update sys.path if needed
#if os.path.join(os.environ['GISBASE'], "etc", "python") not in sys.path:
#    sys.path.append(os.path.join(os.environ['GISBASE'], "etc", "python"))
#    
## update/create PYTHONPATH if needed
#if 'PYTHONPATH' not in os.environ:
#    print 'create PYTHONPATH'
#    os.environ['PYTHONPATH'] = os.path.join(os.environ['GISBASE'], "etc", "python")
#else:
#    if os.path.join(os.environ['GISBASE'], "etc", "python") not in os.environ['PYTHONPATH']:
#        print 'update PYTHONPATH'
#        os.environ['PYTHONPATH'] = os.environ['PYTHONPATH'] + ':' + os.path.join(os.environ['GISBASE'], "etc", "python")
#
#os.environ['GISDBASE'] = os.path.join(envHome,'grassdata')
#
## check for database folder
#if not os.path.exists(os.environ['GISDBASE']):
#    print 'no grassdata folder'
#    sys.exit()
#
## check for current grass session
#gisrc = None
#for x in os.listdir('/tmp'):
#    if x.startswith('grass6'):
#        gisrc = os.path.join('/tmp',x,'gisrc')
#        print 'found current grass session'
#        break
#if not gisrc:
#    # check for rc6 file
#    gisrc = os.path.join(envHome,'.grassrc6')
#    print 'found old grass session'
#    if not os.path.isfile( gisrc ):
#        print "gisrc not found"
#        sys.exit()
#os.environ['GISRC'] = gisrc
#
#
#
#basinrast = 'basin@PERMANENT'
#res = 50
#rfc = 'MB'
#startdate = '2014_06_01'
#enddate = '2014_06_15'
##dirPath = os.path.join('/Volumes/GIS_Rasters/NWS_QPE_Data/renamed')
##==============================================================================
## #######end grass environment
##==============================================================================
import grass.script as grass 
if not os.environ.has_key("GISBASE"):
    grass.message( "You must be in GRASS GIS to run this program." )
    sys.exit(1)

def main():
    
    t0=time.time()
    HOME = expanduser('~')
    
    ########this script extracts recent QPE grids from NMQ site and retains them in .tiff format, averaging values over subbasins, outputs text file of averages
    ##################################change these parameters
    
    basinrast = options['basinrast'].split('@')[0]
    res = options['res'].split('@')[0]
    rfc = 'MB' ####river forecast center MB = missouri river basin NC = red river/devils lake/souris basins
    startdate = options['start_date'].split('@')[0]
    enddate = options['end_date'].split('@')[0]
    dirPath = os.path.join('/Volumes/GIS_Rasters/NWS_QPE_Data/renamed')
    
    #########################################
    
    
    basinlist = []
    filelist = []
    
    
    if not os.environ.has_key("GISBASE"):
        grass.message( "You must be in GRASS GIS to run this program." )
        sys.exit(1)
        
    # Save current region
    grass.read_command('g.region', flags = 'p', save = 'original', overwrite = True)
    
    # Change resolution to res
    cmd = "g.region -g rast=%s res=%s" % (basinrast,res)
    proc = subprocess.Popen( cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ff, err = proc.communicate()
    
    #assign extents
    ymax = (ff.split('\n')[0]).split('=')[1]
    ymin = (ff.split('\n')[1]).split('=')[1]
    xmin = (ff.split('\n')[2]).split('=')[1]
    xmax = (ff.split('\n')[3]).split('=')[1]
    
    #get basin names
    info = grass.parse_command('r.category', map = basinrast)
    for i in info:
        basinlist.append(i.split('\t')[1])
    basinlist.sort()
    numbasins = len(basinlist)
    
    # Read location
    cmd = "g.gisenv"
    proc = subprocess.Popen( cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ff, err = proc.communicate()
    loc =  ff.split("NAME='")[1].split("'")[0]
    temp_dir = os.path.join(HOME,'Desktop','temp_'+loc+'_'+startdate)
    
    #Read projection
    cmd = 'g.proj -j -f'
    proc = subprocess.Popen( cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ff, err = proc.communicate()
    crs = ff
    
    
    if os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir)
        
    os.makedirs(temp_dir)
    
    #change working directory
    os.chdir(dirPath)
    
    
    #Create list of available data files
    
    filelist.extend(glob.glob('*.tar.gz'))
    
    ##convert dates to datetime objects
    startdate_d = datetime.date(int(startdate.split('_')[0]),int(startdate.split('_')[1]),int(startdate.split('_')[2]))-datetime.timedelta(days = 1)
    
    enddate_d = datetime.date(int(enddate.split('_')[0]),int(enddate.split('_')[1]),int(enddate.split('_')[2]))
    
    #check if date range spans data format change 
    if startdate_d <= datetime.date(year=2005,month=9,day=30) <= enddate_d:
        grass.message( 'Data formats change on Oct 1st 2005...Adjust date range and retry')
        sys.exit()
    
    #create list of years of data requested
    yearlist = []
    for i in range(int(enddate_d.year) - int(startdate_d.year)+1):
        tempyear = int(startdate_d.year)+i
        if enddate_d <= datetime.date(year=2005,month=9,day=30):
            yearlist.append(str(int(startdate_d.year)+i)+'_'+rfc)
        else:
            yearlist.append(str(int(startdate_d.year)+i))
    
    for i in yearlist:
    
        grass.message( 'Expanding %s QPE files'%i)
        cmd = 'tar -xf %s.tar.gz -C %s'%(i,temp_dir)
        proc = subprocess.Popen( cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ff, err = proc.communicate()
    
    os.chdir(temp_dir)
    
    #create output file
    out_table = 'precipavg_%s_%s.txt'%(basinrast,startdate)
    fout = open(out_table,'w')
    fout.write( 'datetimeUTC\tdatetimeCDT\tdatatype\t' )
    for i in basinlist:
        fout.write( '%s\t'%i )
    fout.write('\n')
    
    
    first = True
    
    #enter main loop
    
    for root,dir,files in os.walk(temp_dir):
        for name in files:
            #print name
            if (name.endswith('.Z') or name.endswith('.gz')) and 'miss' not in name:
                if len(name.split('.'))>2 and name.split('.')[2].endswith(('06h','24h')):
                    os.remove(os.path.join(root,name))
                    continue
                else:
                    if name.startswith('ST4.'):
                        filename = os.path.join(root,name)
                        datatype = 'stage4'
                        #create datetime object from file name
                        y = int(name.split('.')[1][0:4])
                        m = int(name.split('.')[1][4:6])
                        d = int(name.split('.')[1][6:8])
                        h = int(name.split('.')[1][8:10])
                        ext=name.split('.')[-1]
                        filename = '.'.join(filename.split('.')[0:-1])
                        name = '.'.join(name.split('.')[0:-1])
                        
                    else:
                        filename = os.path.join(root,name)
                        datatype = name.split('.')[0].split('_')[5]
                        
                        #create datetime object from file name
                        y = int(name.split('_')[0])
                        m = int(name.split('_')[1])
                        d = int(name.split('_')[2])
                        h = int(name.split('_')[3][0:2])
                        ext=name.split('.')[-1]
                        filename = filename.split('.')[0]
                        name = name.split('.')[0]
                        
                    
                    dt_utc = datetime.datetime(y,m,d,h)
                    dt_cdt = dt_utc - datetime.timedelta(hours=5)#convert from UTC to CDT
                    
                    #check if first iteration
                    if first:
                        dt_utc_old = dt_utc-datetime.timedelta(hours=1)
                        dt_cdt_old = dt_cdt - datetime.timedelta(hours=1)
                        first = False
                            
                    #check of file is within data window
                    if startdate_d <= datetime.date(year = y, month = m, day = d) <= enddate_d:
                        ####Check for missing data
                        timegap = dt_utc - dt_utc_old
                        if timegap > datetime.timedelta(hours=1):
                            grass.message( 'Missing data, there is a gap of %s' %timegap)
                            timegaplist_temp = range(int(timegap.days*24+timegap.seconds/60/60))
                            for i in timegaplist_temp[1:]:
                                fout.write('%s\t%s\tno data\t%s\n'%(dt_utc_old+datetime.timedelta(hours=(i)),dt_utc_old+datetime.timedelta(hours=(i-5)),'0\t'*len(basinlist)) )#write place holder for missing data
                    
                     
        
                        grass.message( 'Processing %s'%name)
                        
            #            cmd = 'gunzip  '+filename
            #            proc = subprocess.Popen( cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            #            ff, err = proc.communicate()
                        
                        if ext == 'gz':
                            cmd = 'gunzip  '+filename+'.'+ext
                        else:
                            cmd = 'uncompress  '+filename
                        proc = subprocess.Popen( cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        ff, err = proc.communicate()
                        #print err
                        
                        if y >=2013:
                          
                            cmd = '''/Library/Frameworks/GDAL.framework/Programs/gdalwarp -t_srs %r -of GTiff -te %s %s %s %s %s/%s %s.tif'''%(crs,xmin,ymin,xmax,ymax,root, name,name)
                            proc = subprocess.Popen( cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            ff, err = proc.communicate()
                         
                            
                        else:
            
                        #convert XMRG binary to .asc
                            cmd = os.path.join(dirPath,'xmrgtoasc')+' %s %s ster'%(filename,name)
                            proc = subprocess.Popen( cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            ff, err = proc.communicate()
                            print err
                        
                            #warp .asc from HRAP projection to requested prjection, crop to region
                            cmd = '''/Library/Frameworks/GDAL.framework/Programs/gdalwarp -s_srs '+proj=stere +lat_0=90 +lat_ts=60 +lon_0=-105 +k=1 +x_0=0 +y_0=0 +a=6371200 +b=6371200 +units=m +no_defs' -t_srs '%s' -te %s %s %s %s %s.asc %s.tif'''%(crs,xmin,ymin,xmax,ymax,name,name)
                            proc = subprocess.Popen( cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            ff, err = proc.communicate()
                            print err
                            os.remove(name+'.asc')
                        
                        cmd = '''/Library/Frameworks/GDAL.framework/Programs/gdalinfo -mm %s.tif'''%(name)
                        proc = subprocess.Popen( cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        ff, err = proc.communicate()
                        #scan raster to see if precip data exists
            #                 print [ff]
            #                 print len(ff.split('Max')[1].split(',')[1])
            #                 print type(ff.split('Max')[1].split(',')[1])
            #                 print [ff.split('Max')[1]]
                        max_value = float(ff.split('Max=')[1].split(',')[1].split('\n')[0])
                        
                        #remove zero precip raster
                        if max_value/25.4<0.01:
                            os.remove(name+'.tif')
                            fout.write('%s\t%s\t%s\t%s\n' %(dt_utc,dt_cdt,datatype,'0.00\t'*len(basinlist)))
                        else:
                            cmd = 'r.in.gdal input=%s.tif output=temp_rast  --overwrite'%(name)
                            proc = subprocess.Popen( cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            ff, err = proc.communicate()
                            
                            #zonal stats
                            cmd = "r.univar -t map=temp_rast zones=%s" %(basinrast)
                            proc = subprocess.Popen( cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            ff, err = proc.communicate()
                            
                            data1 = ff.split('\n')
                            fields = data1[0].split('|')
                            dict2={}
                            for x in data1[1:-1]:
                                rec1 = x.split('|')
                                dict1 = dict(zip(fields, rec1 ) )
                                basinname = rec1[1]
                                dict2[basinname]=dict1;
                            fout.write('%s\t%s\t%s\t'%(dt_utc, dt_cdt,datatype))
                            for x2 in basinlist:
                                fout.write('%.2f\t'%(float((dict2[x2])['mean'])/25.4))
                            fout.write('\n')
                    else:
                        os.remove(os.path.join(root,name+'.'+ext))
                    
                    dt_utc_old = dt_utc
                    dt_cdt_old = dt_cdt
            else:
                continue
    
    fout.close()
    
    #clean up files
    cmd = "g.remove temp_rast"
    proc = subprocess.Popen( cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ff, err = proc.communicate()
    
    
    # Change resolution to original
    cmd = "g.region region=original"
    proc = subprocess.Popen( cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ff, err = proc.communicate()
    
    
    for i in yearlist:
        shutil.rmtree(i)
    
    t1=time.time()
    tdelta = (t1-t0)/60
    grass.message( '\nFinished - Runtime was %.2f minutes\nData is located at:\n\n%s\n\n\n' % (tdelta, temp_dir))
if __name__ == "__main__":
    options, flags = grass.parser()
    main()
