--[[
Config = {}

Config.min_longitude = -9.258299
Config.max_longitude = -8.895191
Config.min_latitude = 38.397111
Config.max_latitude = 38.703961
Config.raster_data = raster:load(
        '/var/lib/expolis/osrm/pollution.raster',
        Config.min_longitude,
        Config.max_longitude,
        Config.min_latitude,
        Config.max_latitude,
        551, -- num rows
        651  -- num cols
)
Config.weight_osrm = 0.5
Config.weight_pollution = 0.5
]]
local load_raster_data = function (configuration_file, raster_file)
    local Config = {}
    local handler = io.open ("/opt/expolis/etc/" .. configuration_file, "r")

    Config.min_longitude, Config.min_latitude = handler:read ("*n", "*n")
    Config.max_longitude, Config.max_latitude = handler:read ("*n", "*n")
    local number_rows, number_cols = handler:read ("*n", "*n")
    Config.weight_osrm = handler:read ("*n")
    Config.weight_pollution = handler:read ("*n")

    handler:close ()
    Config.raster_data = raster:load(
            "/var/lib/expolis/osrm/" .. raster_file,
            Config.min_longitude,
            Config.max_longitude,
            Config.min_latitude,
            Config.max_latitude,
            number_rows,
            number_cols
    )

    print ("Minimum coordinate ", Config.min_longitude, Config.min_latitude)
    print ("Maximum coordinate ", Config.max_longitude, Config.max_latitude)
    print ("Raster image size ", number_rows, number_cols)
    print (Config)
    return Config
end

return load_raster_data
