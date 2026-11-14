package com.kalabushkin.gym;

import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;

/**
 * A player lying on a weight bench.
 *
 * @param yaw      the yaw the lying body faces (towards its feet)
 * @param repStart world time the last bench press rep started
 */
public record BenchPose(float yaw, long repStart) {
	public static final PacketCodec<ByteBuf, BenchPose> PACKET_CODEC = PacketCodec.tuple(
			PacketCodecs.FLOAT, BenchPose::yaw, PacketCodecs.VAR_LONG, BenchPose::repStart, BenchPose::new);
}
