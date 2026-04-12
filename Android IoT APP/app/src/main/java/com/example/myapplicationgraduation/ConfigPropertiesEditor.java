package com.example.myapplicationgraduation;

import android.os.Environment;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.Properties;

public class ConfigPropertiesEditor {
    File extDir = Environment.getExternalStorageDirectory();
    private String filePath = "config.properties"; //Configuration file path

    public ConfigPropertiesEditor() {
        //Initialize configuration file path
    }

    public void readProperties() {
        try (FileInputStream input = new FileInputStream(new File(filePath))) {
            Properties prop = new Properties();
            prop.load(input);
        } catch (IOException ex) {
            ex.printStackTrace();
        }
    }

    public void writeProperties(String key, String value) {
        try (FileOutputStream output = new FileOutputStream(new File(filePath))) {
            Properties prop = new Properties();
            prop.load(new FileInputStream(filePath));

            //Modify key-value pair
            prop.setProperty(key, value);

            //Save modified configuration file
            prop.store(output, null);
        } catch (IOException ex) {
            ex.printStackTrace();
        }
    }
}

