import xarray as xr
import glob
import sys
import numpy as np
import pandas as pd

def month_converter(infile_month):
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    mask = np.in1d(months, infile_month)
    m_rank = str(np.arange(1,13)[mask][0])
    if len(m_rank) < 2:
        return '0'+m_rank
    else:
        return m_rank

files = glob.glob('SABER*v2.0.nc')
#latitude-altitude grid parameters
lat_b1 = -55
lat_b2 = 65
lat_step = 10
in_year_ls = []
nz = 50; dz = 2.
lev_start = 31.

for item in files:
    print(item)
    in_month  = item [14:-12]
    in_year = item[-12:-8]
    in_year_ls.append(in_year)
    print(in_month, in_year, month_converter(in_month))

    
    ds = xr.open_dataset(item) #open raw SABER file
    da = xr.DataArray(ds.ktemp.values, coords={'lat': (['event','altitude'], ds.tplatitude.values), 'altitude': (['altitude'], ds.tpaltitude.sel(event = 0))}, dims = ['event','altitude'] ) 
    
    lev = np.arange(lev_start,lev_start+nz*dz,dz,float)
    tuples_ls = []
    #generate tuples including layers with 2 km depth
    for z in xrange(nz):
        dum = np.ma.masked_where(da.altitude.values<(lev[z]-1.0), np.arange(da.altitude.shape[0]))
        dum = np.ma.masked_where(da.altitude.values>(lev[z]+1.0),dum)  
        tuples_ls.append(slice(dum.compressed()[0], dum.compressed()[-1]))
    
    vertlevels = [da.isel(altitude=i).groupby_bins('lat', np.arange(lat_b1, lat_b2, lat_step), labels = (np.arange(lat_b1, lat_b2, lat_step)+lat_step/2)[:-1]).mean() for i in tuples_ls]

    xavgvel = xr.concat(vertlevels, 'altitude')
    xavgvel['altitude'] = lev
    xavgvel = xavgvel.rename({'lat_bins': 'lat'})
    xavgvel_ds = xavgvel.to_dataset(name = 'ta')
    xavgvel_ds.to_netcdf('SABER_temp_'+in_year+month_converter(in_month)+'_binned.nc')
    #sys.exit()

in_year_arr = np.array(in_year_ls)
s_year = str(np.min(in_year_arr))
e_year = str(np.max(in_year_arr))
ds = xr.open_mfdataset(infiles, concat_dim='time')
ds['time'] = pd.data_range(start = s_year+'01', periods = ds.time.shape[0], freq = 'M')
ds.to_netcdf('SABER_temp_'+s_year+'01'+'_'+e_year+'12_binned_zm.nc')
