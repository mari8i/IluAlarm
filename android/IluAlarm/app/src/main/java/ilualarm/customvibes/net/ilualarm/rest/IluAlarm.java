package ilualarm.customvibes.net.ilualarm.rest;

import java.util.List;

import ilualarm.customvibes.net.ilualarm.model.Alarm;
import ilualarm.customvibes.net.ilualarm.model.RGB;
import ilualarm.customvibes.net.ilualarm.model.Text;
import ilualarm.customvibes.net.ilualarm.model.Volume;
import retrofit.Call;
import retrofit.http.Body;
import retrofit.http.GET;
import retrofit.http.POST;

/**
 * Created by mariotti on 08/12/15.
 */
public interface IluAlarm {

    @GET("/color/")
    Call<IluAlarmResponse<RGB>> getColor();

    @GET("/snooze/")
    Call<IluAlarmResponse> snooze();

    @GET("/stop/")
    Call<IluAlarmResponse> stop();

    @POST("/color/")
    Call<IluAlarmResponse> setColor(@Body RGB color);

    @GET("/text/")
    Call<IluAlarmResponse<Text>> getText();

    @POST("/text/")
    Call<IluAlarmResponse> setText(@Body Text color);

    @GET("/alarm/")
    Call<IluAlarmResponse<List<Alarm>>> getAlarms();

    @POST("/alarm/")
    Call<IluAlarmResponse<Alarm>> postAlarm(@Body Alarm alarm);

    @GET("/volume/")
    Call<IluAlarmResponse<Volume>> getVolume();

    @POST("/volume/")
    Call<IluAlarmResponse> setVolume(@Body Volume volume);
}
