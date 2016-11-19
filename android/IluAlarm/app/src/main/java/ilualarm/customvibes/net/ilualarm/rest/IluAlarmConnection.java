package ilualarm.customvibes.net.ilualarm.rest;

import android.content.Context;
import android.content.SharedPreferences;
import android.preference.PreferenceManager;

import com.google.gson.FieldNamingPolicy;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.IOException;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

import retrofit.GsonConverterFactory;
import retrofit.Response;
import retrofit.Retrofit;

/**
 * Created by mariotti on 08/12/15.
 */
public class IluAlarmConnection {

    private interface IConnectionJob<T> {
        Response<T> _doCall(IluAlarm conn) throws IOException;
        void _onSuccess(Response<T> data);
        void _onError(Exception e);
    }

    public abstract static class ConnectionJob<T> implements IConnectionJob<T> {

        public Response<T> _doCall(IluAlarm conn) throws IOException {
            return this.doCall(conn);
        }

        public void _onSuccess(Response<T> data) {
            this.onSuccess(data);
        }

        public void _onError(Exception e) {
            this.onError(e);
        }

        public abstract Response<T> doCall(IluAlarm conn) throws IOException;
        public abstract void onSuccess(Response<T> data);
        public abstract void onError(Exception e);
    }

    public abstract static class IluConnectionJob<T>
            implements IConnectionJob<IluAlarmResponse<T>> {

        public void repeat(Context context, IluAlarmConnection conn) {
            if (conn == null || context == null) { return; }
            SharedPreferences prefs = PreferenceManager.getDefaultSharedPreferences(context);
            String res = prefs.getString("update_interval", "5");
            Long update_interval = Long.parseLong(res) * 1000L;
            conn.addCommand(this, update_interval);
        }

        public void retry(Context context, IluAlarmConnection conn) {
            if (conn == null || context == null) { return; }
            SharedPreferences prefs = PreferenceManager.getDefaultSharedPreferences(context);
            String res = prefs.getString("retry_interval", "5");
            Long update_interval = Long.parseLong(res) * 1000L;
            conn.addCommand(this, update_interval);
        }

        public abstract Response<T> doCall(IluAlarm conn) throws IOException;
        public abstract void onSuccess(T data);
        public abstract void onError(Exception e);

        @Override
        public Response _doCall(IluAlarm conn) throws IOException {
            Response<T> tResponse = doCall(conn);
            Response<IluAlarmResponse<T>> res = (Response<IluAlarmResponse<T>>) tResponse;
            return res;
        }

        @Override
        public void _onSuccess(Response<IluAlarmResponse<T>> data) {
            if (!"ok".equals(data.body().getStatus())) {
                this._onError(new Exception("Status is NOT OK "));
            }
            IluAlarmResponse<T> body = data.body();
            this.onSuccess(body.getData());
        }

        @Override
        public void _onError(Exception e) {
            this.onError(e);
        }
    }

    private final IluAlarm conn;
    private final LinkedBlockingQueue<Runnable> syncJobs;
    private final ThreadPoolExecutor pool;

    public IluAlarmConnection(Context context) {
        this.conn = createConnection(context);

        syncJobs = new LinkedBlockingQueue<>();
        pool = new ThreadPoolExecutor(1, 1, 1, TimeUnit.SECONDS, syncJobs);
    }

    public IluAlarm createConnection(Context context) {
        SharedPreferences prefs = PreferenceManager.getDefaultSharedPreferences(context);

        // 2015-12-08T19:53:01.170037
        Gson gson = new GsonBuilder()
                .setDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS")
                .setFieldNamingPolicy(FieldNamingPolicy.LOWER_CASE_WITH_UNDERSCORES)
                .create();

        Retrofit retrofit = new Retrofit.Builder()
                .baseUrl("http://" + prefs.getString("device_url", "192.168.1.7") + ":" + prefs.getString("device_port", "8111"))
                .addConverterFactory(GsonConverterFactory.create(gson))
                .build();

        return retrofit.create(IluAlarm.class);
    }

    public void addCommand(final IConnectionJob job) {
        addCommand(job, null);
    }

    public void addCommand(final IConnectionJob job, final Long delay) {
        final Runnable runnable = new Runnable() {
            @Override
            public void run() {
                try {
                    Response response = job._doCall(conn);
                    job._onSuccess(response);
                }
                catch(Exception e) {
                    job._onError(e);
                }
            }
        };

        if (delay == null) {
            try {
                pool.execute(runnable);
            } catch (Exception e) {
                // Pool has probably been shut down..
                System.out.println("---> KNOWN EXCEPTION S");
                e.printStackTrace();
                System.out.println("---> KNOWN EXCEPTION E");
            }
        }
        else {
            new Thread() {
                @Override
                public void run() {
                    try {
                        Thread.sleep(delay);
                    } catch (InterruptedException e) {
                        return;
                    }
                    try {
                        pool.execute(runnable);
                    } catch (Exception e) {
                        // Pool has probably been shut down..
                        System.out.println("---> KNOWN EXCEPTION S");
                        e.printStackTrace();
                        System.out.println("---> KNOWN EXCEPTION E");
                    }
                }
            }.start();
        }

    }

    public void purgeAll() {
        pool.shutdownNow();
    }


    @Override
    protected void finalize() throws Throwable {
        pool.shutdownNow();
        super.finalize();
    }
}
