package com.example.myapplicationgraduation;

import android.app.Activity;
import android.content.ContentValues;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Message;
import android.view.View;
import android.widget.Button;
import android.widget.SeekBar;
import android.widget.TextView;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Timer;
import java.util.TimerTask;

public class CurtainActivity extends Activity {
    private SQLiteDatabase db;
    private DatabaseHelper databaseHelper;
    private TextView tv_switch_status_light;
    private TextView tv_switch_status_curtain;
    private TextView tv_brightness_threshold;
    private SeekBar s_brightness_threshold_seekbar;
    private Button b_curtain_open;
    private Button b_curtain_close;

    int brightness_threshold_value = 0;
    private String[] data = {"0","0","0"};

    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_curtain);
        setTitle("智能窗帘");

        DatabaseHelper databaseHelper = new DatabaseHelper(this,"iot_db",null,1);
        db = databaseHelper.getWritableDatabase();

        tv_switch_status_light = (TextView)findViewById(R.id.switch_status_view_light);
        tv_switch_status_curtain = (TextView)findViewById(R.id.switch_status_view_curtain);
        tv_brightness_threshold = (TextView)findViewById(R.id.brightness_threshold_view);

        s_brightness_threshold_seekbar = (SeekBar)findViewById(R.id.brightness_threshold_seekbar);

        b_curtain_open = (Button)findViewById(R.id.curtain_open);
        b_curtain_close = (Button)findViewById(R.id.curtain_close);

        s_brightness_threshold_seekbar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {}

            @Override
            public void onStartTrackingTouch(SeekBar seekBar) {}

            @Override
            public void onStopTrackingTouch(SeekBar seekBar) {
                brightness_threshold_value = s_brightness_threshold_seekbar.getProgress();
                brightness_threshold_value = brightness_threshold_value * 20;
                new Thread(new Runnable() {
                    @Override
                    public void run() {
                        try {
                            MyComm myComm = new MyComm();
                            MySocket.sendInfo(myComm.format_comm_data("change_brightness_threshold",Integer.toString(brightness_threshold_value),"1"));
                        }catch (Exception e){
                            e.printStackTrace();
                        }
                    }
                }).start();
            }
        });
        start_auto_seekBar_view_thread("brightness");

        b_curtain_open.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                new Thread(new Runnable() {
                    @Override
                    public void run() {
                        try {
                            MyComm myComm = new MyComm();
                            MySocket.sendInfo(myComm.format_comm_data("curtain_open","1","1"));
                        }catch (Exception e){
                            e.printStackTrace();
                        }
                    }
                }).start();
            }
        });

        b_curtain_close.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                new Thread(new Runnable() {
                    @Override
                    public void run() {
                        try {
                            MyComm myComm = new MyComm();
                            MySocket.sendInfo(myComm.format_comm_data("curtain_close","0","1"));
                        }catch (Exception e){
                            e.printStackTrace();
                        }
                    }
                }).start();
            }
        });

        TimerTask task = new TimerTask() {
            @Override
            public void run() {
                getInfo();
            }
        };
        Timer timer = new Timer();
        timer.scheduleAtFixedRate(task, 1500,1500);

    }
    Handler handler = new Handler(){
        public void handleMessage(Message msg){
            super.handleMessage(msg);
            refreshData(msg.getData().getString("info"));
            refreshViews();
        }
    };

    private void start_auto_seekBar_view_thread(String tv_name) {
        final Handler handler = new Handler(Looper.getMainLooper());
        new Thread(new Runnable() {
            @Override
            public void run() {
                while (true) {
                    handler.post(new Runnable() {
                        @Override
                        public void run() {
                            if (tv_name.equals("brightness"))
                                tv_brightness_threshold.setText(String.valueOf(brightness_threshold_value));
                        }
                    });

                    try {
                        Thread.sleep(1); // 更新间隔，例如每秒更新一次
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }
            }
        }).start();
    }

    protected void getInfo(){
        try {
            final String info = MySocket.getInfo();
            new Thread(new Runnable() {
                @Override
                public void run() {
                    Message msg = new Message();
                    Bundle bundle = new Bundle();
                    bundle.putString("info",info);
                    msg.setData(bundle);
                    handler.sendMessage(msg);
                }
            }).start();
        }catch (Exception e){
            e.printStackTrace();
        }

    }

    private void refreshData(String info){
        JSONObject jsonObject = (JSONObject) JSON.parse(info);

        // 严格对应Python网关处data_from_source中各个字典键名
        data[0] = jsonObject.getString("Light_CU");
        data[1] = jsonObject.getString("Brightness");
        data[2] = jsonObject.getString("Curtain_status");

        // 插入历史记录数据库
        ContentValues values = new ContentValues();
        SimpleDateFormat format = new SimpleDateFormat("yyyy - MM - dd HH:mm:ss");
        Date time = new Date();
        String d = format.format(time);
        Date date = null;
        try {
            date = format.parse(d);
        }catch (Exception e){
            e.printStackTrace();
        }

        values.put("time", date.getTime());
        values.put("light_cu",data[0]);
        values.put("brightness",data[1]);
        values.put("curtain_status",data[2]);
        db.insert("history_data",null,values);
    }

    private void refreshViews(){
        tv_switch_status_curtain.setText(data[0].equals("1")?"开启":"关闭");
        tv_switch_status_light.setText(data[2].equals("1")?"开启":"关闭");
    }

}
