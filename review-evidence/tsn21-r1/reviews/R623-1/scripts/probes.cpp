TEST_F(AcmpCore, R623PublicationPrecedesBlockedSendAndQueue) {
    fk.room = false;
    fk.pub_hook = [this] {
        EXPECT_EQ(a.owed_count, 0u) << "R623 publication precedes queue insertion";
        EXPECT_EQ(fk.count(Call::SEND), 0u) << "R623 publication precedes blocked send attempt";
    };
    bind(0);
    ASSERT_EQ(fk.pubs.size(), 1u);
    EXPECT_TRUE(published_before_send(0, 0));
    EXPECT_TRUE(fk.sent.empty());
    EXPECT_EQ(a.owed_count, 2u);
    EXPECT_TRUE(acmp_poll(&a));
    EXPECT_EQ(fk.pubs.size(), 1u);
    fk.room = true;
    EXPECT_TRUE(acmp_poll(&a));
    EXPECT_FALSE(acmp_poll(&a));
    EXPECT_EQ(fk.sent.size(), 2u);
    EXPECT_EQ(fk.pubs.size(), 1u) << "R623 queued retries preserve publication cache";
}

TEST_F(AcmpCore, R623CompletionPublicationPrecedesOtherCallbacks) {
    bind(0);
    fk.clear();
    rx(probe_answer(0));
    ASSERT_EQ(fk.pubs.size(), 1u);
    ASSERT_GE(fk.position(Call::TIMER), 0);
    EXPECT_LE(fk.pubs[0].before, static_cast<std::size_t>(fk.position(Call::TIMER)))
        << "R623 settlement publication precedes timer callback";
    fk.clear();
    ASSERT_TRUE(acmp_set_started(&a, 0, false));
    ASSERT_EQ(fk.pubs.size(), 1u);
    ASSERT_GE(fk.position(Call::PERSIST), 0);
    ASSERT_GE(fk.position(Call::CHANGED), 0);
    EXPECT_LE(fk.pubs[0].before, static_cast<std::size_t>(fk.position(Call::PERSIST)))
        << "R623 stopped publication precedes persistence";
    EXPECT_LE(fk.pubs[0].before, static_cast<std::size_t>(fk.position(Call::CHANGED)))
        << "R623 stopped publication precedes notification";
    EXPECT_TRUE(fk.sent.empty());
    EXPECT_FALSE(fk.pubs[0].moved);
    EXPECT_EQ(fk.pubs[0].stream, kSid);
}

TEST_F(AcmpCore, R623AllRestoredSinksPublishBeforeAdmission) {
    const auto record = payload(kRecValid | kRecStarted, 1u, kTkB, kCtl1);
    for (unsigned k = 0; k < 3; ++k) {
        ASSERT_EQ(acmp_restore_binding(&a, k, record.data(), record.size()), ACMP_RESTORE_APPLIED);
    }
    EXPECT_TRUE(fk.pubs.empty());
    acmp_open(&a);
    ASSERT_EQ(fk.pubs.size(), 3u);
    ASSERT_GE(fk.position(Call::ADMIT), 0);
    for (unsigned k = 0; k < 3; ++k) {
        EXPECT_EQ(fk.pubs[k].sink, k);
        EXPECT_EQ(fk.pubs[k].interface, k == 2 ? 1u : 0u);
        EXPECT_TRUE(fk.pubs[k].bound && fk.pubs[k].started);
        EXPECT_EQ(fk.pubs[k].stream, 0u);
        EXPECT_LE(fk.pubs[k].before, static_cast<std::size_t>(fk.position(Call::ADMIT)))
            << "R623 all restored publications precede admission";
    }
    fk.clear();
    acmp_restore_rollback(&a);
    EXPECT_TRUE(fk.pubs.empty());
    acmp_open(&a);
    ASSERT_EQ(fk.pubs.size(), 3u);
    for (const auto& pub : fk.pubs) EXPECT_FALSE(pub.bound || pub.started);
}
