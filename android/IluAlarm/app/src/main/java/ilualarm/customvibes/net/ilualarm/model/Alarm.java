package ilualarm.customvibes.net.ilualarm.model;

import java.io.Serializable;
import java.util.Date;

/**
 * Created by mariotti on 08/12/15.
 */
public class Alarm implements Serializable {

    public static final int TYPE_SCHEDULED = 0;
    public static final int TYPE_ALARM = 1;

    private int type;
    private String tag;
    private int id = -1;
    private String name;
    private String message;
    private boolean enabled;
    private Date time;
    private Date setTime;
    private Integer repeatEvery;
    private Integer timeout;


    public int getType() {
        return type;
    }

    public void setType(int type) {
        this.type = type;
    }

    private boolean isTimer() {
        return this.type == TYPE_ALARM;
    }

    private boolean isScheduled() {
        return this.type == TYPE_SCHEDULED;
    }

    public String getTag() {
        return tag;
    }

    public void setTag(String tag) {
        this.tag = tag;
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public boolean isEnabled() {
        return enabled;
    }

    public void setEnabled(boolean enabled) {
        this.enabled = enabled;
    }

    public Date getTime() {
        return time;
    }

    public void setTime(Date time) {
        this.time = time;
    }

    public Date getSetTime() {
        return setTime;
    }

    public void setSetTime(Date setTime) {
        this.setTime = setTime;
    }

    public Integer getRepeatEvery() {
        return repeatEvery;
    }

    public void setRepeatEvery(Integer repeatEvery) {
        this.repeatEvery = repeatEvery;
    }

    public Integer getTimeout() {
        return timeout;
    }

    public void setTimeout(Integer timeout) {
        this.timeout = timeout;
    }
}

