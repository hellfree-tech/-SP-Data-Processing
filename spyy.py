import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import griddata

def dms_to_dd(d, m, s):
    """Converts Degrees, Minutes, Seconds to Decimal Degrees."""
    return d + m / 60.0 + s / 3600.0

def interpolate_coordinates(start_coord, end_coord, max_length, target_distances):
    """
    Interpolates DMS coordinates lineally along the traverse 
    based on the profile midpoint distance values.
    """
    start_lat = dms_to_dd(*start_coord['lat'])
    start_lon = dms_to_dd(*start_coord['lon'])
    end_lat = dms_to_dd(*end_coord['lat'])
    end_lon = dms_to_dd(*end_coord['lon'])
    
    # Calculate fraction along the total measured line length
    fractions = np.array(target_distances) / max_length
    
    interp_lats = start_lat + (end_lat - start_lat) * fractions
    interp_lons = start_lon + (end_lon - start_lon) * fractions
    
    return interp_lats, interp_lons

def plot_traverse_sp(excel_file, start_coord, end_coord, traverse_length, traverse_name="Traverse 1"):
    # 1. Read external Excel spreadsheet 
    df = pd.read_excel(excel_file)
    
    # Clean up column names to avoid trailing whitespaces
    df.columns = [str(c).strip() for c in df.columns]
    
    midpoints = df['Midpoint'].values
    a_spacings = [5, 10, 15, 20, 25, 30]
    
    # Generate spatial lat/lon coordinates for each midpoint marker
    lats, lons = interpolate_coordinates(start_coord, end_coord, traverse_length, midpoints)
    
    # Restructure data arrays for mapping
    X_dist = [] # Midpoint distance profile line
    Y_a = []    # Electrode spacing 'a' (acts as pseudodepth indicator)
    Z_sp = []   # Raw Self-Potential reading value
    Lat_arr = []
    Lon_arr = []
    
    for i, mid in enumerate(midpoints):
        for a in a_spacings:
            col_name = f"a={a}"
            if col_name in df.columns:
                X_dist.append(mid)
                Y_a.append(a)
                Z_sp.append(df.loc[i, col_name])
                Lat_arr.append(lats[i])
                Lon_arr.append(lons[i])
                
    X_dist = np.array(X_dist)
    Y_a = np.array(Y_a)
    Z_sp = np.array(Z_sp)
    Lat_arr = np.array(Lat_arr)
    Lon_arr = np.array(Lon_arr)

    # Convert spacing to negative values for downward pseudodepth profile tracking
    depth_values = -Y_a
    depth_factor = 1.34  # Geometric tracking scale modifier
    scaled_depths = depth_values * depth_factor
    
    start_lat_dd = dms_to_dd(*start_coord['lat'])
    start_lon_dd = dms_to_dd(*start_coord['lon'])
    end_lat_dd = dms_to_dd(*end_coord['lat'])
    end_lon_dd = dms_to_dd(*end_coord['lon'])

    # ------------------ 2D PLOT SETUP (MAPPED TO LATITUDE COORDINATE) ------------------
    grid_lat = np.linspace(start_lat_dd, end_lat_dd, 200)
    grid_depth_2d = np.linspace(scaled_depths.min(), 0, 100)
    GRID_LAT_2D, GRID_DEPTH_2D = np.meshgrid(grid_lat, grid_depth_2d)
    
    # Interpolate SP on the 2D plane (Latitude vs Depth)
    GRID_SP_2D = griddata((Lat_arr, scaled_depths), Z_sp, (GRID_LAT_2D, GRID_DEPTH_2D), method='linear')
    
    # Symmetrical slant formula on both left and right edges
    rows_2d, cols_2d = GRID_SP_2D.shape
    lat_min, lat_max = start_lat_dd, end_lat_dd
    lat_range = lat_max - lat_min
    max_depth = scaled_depths.min()
    
    for i in range(rows_2d):
        for j in range(cols_2d):
            current_lat = GRID_LAT_2D[i, j]
            current_depth = GRID_DEPTH_2D[i, j]
            
            fraction_from_edge = min(current_lat - lat_min, lat_max - current_lat) / (lat_range / 2.0)
            fraction_from_edge = np.clip(fraction_from_edge, 0, 1)
            
            boundary_depth = max_depth * fraction_from_edge
            if current_depth < boundary_depth:
                GRID_SP_2D[i, j] = np.nan

    # ------------------ GENERATE 2D CONTOUR PLOT PANEL ------------------
    fig2d, ax2d = plt.subplots(figsize=(12, 5))
    contour2d = ax2d.contourf(GRID_LAT_2D, GRID_DEPTH_2D, GRID_SP_2D, levels=20, cmap='jet')
    
    ax2d.set_title(f"2D SP Coordinate Pseudosection — {traverse_name}", fontsize=14, weight='bold', pad=15)
    ax2d.set_xlabel("Latitude Coordinate (Decimal Degrees)", fontsize=11, labelpad=10)
    ax2d.set_ylabel("Depth (m)", fontsize=11, labelpad=10)
    ax2d.grid(True, linestyle=':', alpha=0.6)
    
    cbar2d = fig2d.colorbar(contour2d, ax=ax2d, orientation='horizontal', pad=0.2, shrink=0.7)
    cbar2d.set_label("Self-potential, mV", fontsize=11)
    
    ax2d.text(start_lat_dd, max(GRID_DEPTH_2D.max(), 1), f"START\n{start_coord['lat']}°N\n{start_coord['lon']}°E", ha='center', fontsize=8)
    ax2d.text(end_lat_dd, max(GRID_DEPTH_2D.max(), 1), f"END\n{end_coord['lat']}°N\n{end_coord['lon']}°E", ha='center', fontsize=8)
    
    # ------------------ GENERATE 3D VOLUMETRIC BLOCK MODEL ------------------
    fig3d = plt.figure(figsize=(14, 9))
    ax3d = fig3d.add_subplot(projection='3d')
    
    # To mimic a full 3D voxel block volume model from a single profile line,
    # we extrude the 2D section matrix along a cross-profile width offset vector.
    extrusion_width = 0.0003  # Roughly 30 meters offset in decimal degrees width
    w_steps = 15
    w_offsets = np.linspace(-extrusion_width/2, extrusion_width/2, w_steps)
    
    # Determine profile azimuth direction to offset perpendicular to the line path
    delta_lat = end_lat_dd - start_lat_dd
    delta_lon = end_lon_dd - start_lon_dd
    line_angle = np.arctan2(delta_lat, delta_lon)
    perp_angle = line_angle + np.pi/2.0
    
    # Compute normalized SP colors safely bypassing NaN locations
    valid_mask = ~np.isnan(GRID_SP_2D)
    min_sp_val = np.nanmin(GRID_SP_2D) if np.any(valid_mask) else 0
    max_sp_val = np.nanmax(GRID_SP_2D) if np.any(valid_mask) else 1
    norm_colors = (GRID_SP_2D - min_sp_val) / (max_sp_val - min_sp_val)
    norm_colors = np.clip(norm_colors, 0, 1)
    color_mapped = plt.cm.jet(norm_colors)
    
    # Reconstruct the 2D profile coordinates array
    grid_dist_2d = np.linspace(0, traverse_length, 200)
    GRID_DIST_M, _ = np.meshgrid(grid_dist_2d, grid_depth_2d)
    BASE_LAT = start_lat_dd + (end_lat_dd - start_lat_dd) * (GRID_DIST_M / traverse_length)
    BASE_LON = start_lon_dd + (end_lon_dd - start_lon_dd) * (GRID_DIST_M / traverse_length)
    
    # Extrude layer slices sequentially to compile a solid structural block volume model
    for w in w_offsets:
        offset_lon = BASE_LON + w * np.cos(perp_angle)
        offset_lat = BASE_LAT + w * np.sin(perp_angle)
        
        # Plot continuous thin block slices stacked tightly together
        ax3d.plot_surface(offset_lon, offset_lat, GRID_DEPTH_2D, facecolors=color_mapped,
                                 rcount=100, ccount=50, shade=False, linewidth=0, antialiased=True, alpha=0.9)
    
    # Draw dark wireframe bounding outline boxes to anchor the block appearance
    w_min, w_max = w_offsets[0], w_offsets[-1]
    corner_lons = [
        start_lon_dd + w_min*np.cos(perp_angle), start_lon_dd + w_max*np.cos(perp_angle),
        end_lon_dd + w_max*np.cos(perp_angle), end_lon_dd + w_min*np.cos(perp_angle)
    ]
    corner_lats = [
        start_lat_dd + w_min*np.sin(perp_angle), start_lat_dd + w_max*np.sin(perp_angle),
        end_lat_dd + w_max*np.sin(perp_angle), end_lat_dd + w_min*np.sin(perp_angle)
    ]
    
    # Draw bottom boundary ring box line frames
    z_bottom = GRID_DEPTH_2D.min()
    ax3d.plot(corner_lons + [corner_lons[0]], corner_lats + [corner_lats[0]], z_bottom, color='black', lw=1.5, alpha=0.7)
    # Draw top surface boundary ring box line frames
    ax3d.plot(corner_lons + [corner_lons[0]], corner_lats + [corner_lats[0]], 0, color='black', lw=1.5, alpha=0.7)
    # Connect vertical pillar outline corners
    for clon, clat in zip(corner_lons, corner_lats):
        ax3d.plot([clon, clon], [clat, clat], [z_bottom, 0], color='black', lw=1.5, alpha=0.7)
        
    # Formatting axes ticks, labels, and perspective angles to look exactly like the reference model box
    ax3d.set_title(f"3D Solid Voxel Block Volume Model — {traverse_name}", fontsize=14, weight='bold', pad=25)
    ax3d.set_xlabel("Longitude (Decimal Degrees)", labelpad=15, fontweight='bold')
    ax3d.set_ylabel("Latitude (Decimal Degrees)", labelpad=15, fontweight='bold')
    ax3d.set_zlabel("Subterranean Depth (m)", labelpad=10, fontweight='bold')
    
    # Apply a high-angle axonometric view angle to get full depth box visualization
    ax3d.view_init(elev=30, azim=-50)
    
    # Render right-side scale bar legend layout matching figure panels
    m = plt.cm.ScalarMappable(cmap=plt.cm.jet)
    m.set_array(Z_sp)
    cbar3d = fig3d.colorbar(m, ax=ax3d, pad=0.08, shrink=0.6)
    cbar3d.set_label("Self Potential Reading (mV)", fontsize=11, fontweight='bold')
    
    plt.show()

# ==============================================================================
# USER ENTRY RUNTIME CONFIGURATION (Modify this block per individual Traverse)
# ==============================================================================
if __name__ == "__main__":
    
    # Input files path setting
    excel_path = "TR2_sp.xlsx" 
    
    # Total length definition (e.g., 200, 300, or 400 meters)
    traverse_total_length = 300 
    
    # Supply your Beginning & Ending Coordinates in DMS format: (Degrees, Minutes, Seconds)
    start_point = {
        'lat': (6, 30, 17.26),  
        'lon': (3, 23, 34.99)   
    }
    
    end_point = {
        'lat': (6, 30, 30.17),  
        'lon': (3, 23, 37.64)   
    }
    
    # Execute visualization run for the active traverse configuration
    plot_traverse_sp(
        excel_file=excel_path,
        start_coord=start_point,
        end_coord=end_point,
        traverse_length=traverse_total_length,
        traverse_name="Traverse 2"
    )
