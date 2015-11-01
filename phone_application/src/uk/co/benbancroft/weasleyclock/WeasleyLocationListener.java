package uk.co.benbancroft.weasleyclock;

import android.location.Address;
import android.location.Geocoder;
import android.location.Location;
import android.location.LocationListener;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Toast;

import java.io.IOException;
import java.util.List;
import java.util.Locale;

/**
 * Created by ben on 31/10/15.
 */
public class WeasleyLocationListener implements LocationListener {

    public Location getNewLocation() {
        Location returnLocation = location;
        //location = null;
        return returnLocation;
    }

    private Location location;

    @Override
    public void onLocationChanged(Location loc) {
        this.location = loc;
    }

    @Override
    public void onProviderDisabled(String provider) {}

    @Override
    public void onProviderEnabled(String provider) {}

    @Override
    public void onStatusChanged(String provider, int status, Bundle extras) {}
}
