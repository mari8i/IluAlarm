package ilualarm.customvibes.net.ilualarm.rest;

/**
 * Created by mariotti on 08/12/15.
 */
public class IluAlarmResponse<T> {
    private String status;
    private T data;

    public String getStatus() {
        return status;
    }

    public T getData() {
        return data;
    }
}
